# application/marketplace/views.py
# View functions for the marketplace app.
# Created by Subreet Singh on 04-09-2026

import os
import uuid
from pathlib import Path

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import IntegrityError
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.urls import reverse
from .models import Category, Listing, ListingIntent, ListingType, Message, Role, User
from .forms import RegisterForm


User = get_user_model()

CONDITION_CHOICES = [
    ("new", "New"),
    ("like_new", "Like New"),
    ("good", "Good"),
    ("fair", "Fair"),
    ("poor", "Poor"),
]

# Live listings use ListingIntent; legacy rows may still have status/intent "active".
LIVE_LISTING_INTENTS = frozenset(ListingIntent.values)
LEGACY_LIVE_LISTING_STATUS = "active"


def _save_uploaded_image(image_file):

    if not image_file:
        return None
    original_name = image_file.name or "image"
    ext = Path(original_name).suffix.lower()
    if ext not in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
        ext = ".jpg"

    unique_name = f"{uuid.uuid4().hex}{ext}"

    save_dir = settings.MEDIA_ROOT
    os.makedirs(save_dir, exist_ok=True)
    save_path = os.path.join(save_dir, unique_name)

    with open(save_path, "wb") as f:
        for chunk in image_file.chunks():
            f.write(chunk)

    return f"{settings.MEDIA_URL}{unique_name}"


def base_context():
    return {
        "categories": Category.objects.all().order_by("category_name"),
    }


def _get_logged_in_user(request):
    """Return the User object from Django's auth session, or None."""
    # Use request.user which is automatically set by Django's auth system
    if request.user.is_authenticated:
        return request.user
    return None


def get_marketplace_user(auth_user):
    """Ensure required marketplace fields exist on the auth user.

    This project uses a custom `AUTH_USER_MODEL` (marketplace.User). Historically
    we had logic that tried to "create" a separate marketplace user record.
    That would create duplicate rows and can trigger integrity errors.
    """
    if not auth_user or not auth_user.is_authenticated:
        return None

    changed_fields = []

    if not getattr(auth_user, "sfsu_email", None):
        candidate_emails = []

        inferred_email = (auth_user.email or "").strip().lower()
        if inferred_email:
            candidate_emails.append(inferred_email)

        fallback_email = f"{auth_user.username}@sfsu.edu"
        if fallback_email not in candidate_emails:
            candidate_emails.append(fallback_email)

        for candidate_email in candidate_emails:
            if not User.objects.filter(sfsu_email__iexact=candidate_email).exclude(pk=auth_user.pk).exists():
                auth_user.sfsu_email = candidate_email
                changed_fields.append("sfsu_email")
                break

    if not (auth_user.email or "").strip():
        auth_user.email = auth_user.sfsu_email
        changed_fields.append("email")

    if not getattr(auth_user, "password_hash", None):
        auth_user.password_hash = auth_user.password
        changed_fields.append("password_hash")

    if getattr(auth_user, "role", None) is None:
        role, _ = Role.objects.get_or_create(role_name="student")
        auth_user.role = role
        changed_fields.append("role")

    if changed_fields:
        try:
            auth_user.save(update_fields=changed_fields)
        except IntegrityError:
            pass

    return auth_user


def marketplace_home(request):
    context = base_context()
    context.update({
        "recent_listings": Listing.objects.select_related("category", "seller").order_by("-created_at")[:8],
        "popular_services": Listing.objects.select_related("category", "seller")
            .filter(listing_type="service", intent="for_sale")
            .exclude(description__exact="")
            .order_by("-created_at")[:4],
        "user": _get_logged_in_user(request),
    })
    return render(request, "marketplace/home.html", context)


# --- Authentication views ---

def login_view(request):
    """
    Handle user login via username or email.
    Uses custom EmailOrUsernameBackend for authentication.
    Provides specific error messages for debugging.
    """
    next_page = request.POST.get("next") or request.GET.get("next", "")

    if request.user.is_authenticated:
        return redirect(next_page or "marketplace_home")

    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username_or_email or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, "marketplace/login.html", {"next": next_page})

        # Check if user exists (by username or email)
        user_exists = User.objects.filter(
            Q(username=username_or_email) | Q(email__iexact=username_or_email)
        ).exists()

        if not user_exists:
            messages.error(request, "Username or email not found.")
            return render(request, "marketplace/login.html", {"next": next_page})

        # Attempt authentication with custom backend
        user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            login(request, user)
            get_marketplace_user(user)
            return redirect(next_page or "marketplace_home")
        else:
            # User exists but password is incorrect
            messages.error(request, "Incorrect password.")

    return render(request, "marketplace/login.html", {"next": next_page})


def register_view(request):
    """
    Handle user registration with comprehensive backend validation.
    Validates username, email (@sfsu.edu domain), and password requirements.
    Password is hashed using Django's default PBKDF2 hasher.
    Auto-logs in user after successful registration.
    """
    next_page = request.POST.get("next") or request.GET.get("next", "")

    if request.user.is_authenticated:
        return redirect(next_page or "marketplace_home")

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Save user with hashed password
            user = form.save(commit=True)

            # Create/ensure marketplace user record exists
            get_marketplace_user(user)

            # Auto-login after registration
            login(request, user)
            messages.success(request, "Account created successfully!")

            return redirect(next_page or "marketplace_home")
        else:
            # Form validation errors will be displayed in template
            # Errors from RegisterForm include: username uniqueness, email domain, password strength
            pass

    else:
        form = RegisterForm()

    return render(request, "marketplace/register.html", {
        "form": form,
        "next": next_page,
    })


def _marketplace_context(**extra_context):
    return extra_context


def _parse_decimal(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def _parse_category_ids(raw_category_ids):
    category_ids = []
    for raw_category_id in raw_category_ids:
        try:
            category_ids.append(int(raw_category_id))
        except (TypeError, ValueError):
            continue
    return category_ids


def logout_view(request):
    logout(request)
    return redirect("marketplace_home")


# --- Search ---

def search_results_view(request):
    query        = (request.GET.get("q") or request.GET.get("query") or "").strip()
    listing_type = (request.GET.get("type") or "all").strip().lower()
    date_order   = (request.GET.get("date") or "newest").strip().lower()
    intent       = (request.GET.get("intent") or "all").strip().lower()
    category     = (request.GET.get("category") or "all").strip()

    listings = Listing.objects.select_related("category").all()

    if category != "all":
        listings = listings.filter(category__category_name=category)

    if listing_type in {"product", "service"}:
        listings = listings.filter(listing_type=listing_type)

    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    if date_order == "oldest":
        listings = listings.order_by("created_at")
    else:
        date_order = "newest"
        listings = listings.order_by("-created_at")

    total_count = listings.count()

    paginator = Paginator(listings, 8)
    page_obj = paginator.get_page(request.GET.get("page", 1))

    db_categories = Category.objects.all().order_by("category_name")
    date_order = (request.GET.get("date") or "newest").strip().lower()
    intent = (request.GET.get("intent") or "all").strip().lower()
    selected_category_ids = _parse_category_ids(request.GET.getlist("categories"))
    price_min = _parse_decimal(request.GET.get("price_min"))
    price_max = _parse_decimal(request.GET.get("price_max"))

    results = Listing.objects.select_related('category').all()

    if query:
        results = results.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(category__category_name__icontains=query)
        )

    if listing_type in ListingType.values:
        results = results.filter(listing_type=listing_type)
    else:
        listing_type = 'all'

    if intent == 'offered':
        intent = ListingIntent.FOR_SALE

    if intent in ListingIntent.values:
        results = results.filter(intent=intent)
    else:
        intent = 'all'

    if selected_category_ids:
        results = results.filter(category_id__in=selected_category_ids)

    if price_min is not None:
        results = results.filter(price__gte=price_min)

    if price_max is not None:
        results = results.filter(price__lte=price_max)

    if date_order == 'oldest':
        results = results.order_by('created_at', 'listing_id')
    else:
        date_order = 'newest'
        results = results.order_by('-created_at', '-listing_id')

    return render(request, "marketplace/search_results.html", {
        "page_title": f"Results for {query}" if query else "Search Results",
        "results": page_obj,
        "page_obj": page_obj,
        "query": query,
        "listing_type": listing_type,
        "date_order": date_order,
        "category": category,
        "categories": db_categories,
        "results_count": total_count,
        "user": request.user,
        "intent": intent,
        "selected_category_ids": [str(category_id) for category_id in selected_category_ids],
        "price_min": price_min,
        "price_max": price_max,
    })


# --- Listing CRUD ---

def create_listing_view(request):
    user = request.user
    if not request.user.is_authenticated:
        messages.error(request, "You must be logged in to create a listing.")
        return redirect("login")

    def _create_form_context(post=None):
        ctx = base_context()
        ctx.update({
            "user": user,
            "listing_types": ListingType.choices,
            "listing_intents": ListingIntent.choices,
            "conditions": CONDITION_CHOICES,
            "form": post or {},
        })
        return ctx

    market_user = request.user

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "0")
        listing_type = request.POST.get("listing_type", ListingType.PRODUCT)
        status = request.POST.get("status", "active")
        condition = request.POST.get("condition", "good")
        category_id = request.POST.get("category", "")
        main_picture_url = request.POST.get("main_picture_url", "").strip()

        # Handle uploaded image files — save all; first becomes the thumbnail
        uploaded_images = request.FILES.getlist("images")
        saved_image_urls = []
        for img_file in uploaded_images:
            url = _save_uploaded_image(img_file)
            if url:
                saved_image_urls.append(url)
        if saved_image_urls:
            main_picture_url = saved_image_urls[0]

        if not title:
            messages.error(request, "Title is required.")
            return render(request, "marketplace/create_listing.html", _create_form_context(request.POST))

        if listing_type not in ListingType.values:
            messages.error(request, "Invalid listing type.")
            return render(request, "marketplace/create_listing.html", _create_form_context(request.POST))

        try:
            price_val = round(float(price), 2)
        except ValueError:
            price_val = 0.00

        try:
            cat = Category.objects.get(category_id=category_id)
        except (Category.DoesNotExist, ValueError):
            cat = Category.objects.first()

        listing = Listing.objects.create(
            title=title,
            description=description,
            price=price_val,
            listing_type=listing_type,
            condition=condition,
            category=cat,
            seller=market_user,
            intent=status,
            main_picture_url=main_picture_url or None,
        )
        listing.save()
        messages.success(request, "Listing created!")
        return redirect("listing_detail", listing_id=listing.listing_id)

    context = base_context()
    context["user"] = market_user or user
    return render(request, "marketplace/create_listing.html", _create_form_context())


def category_listings_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = Listing.objects.select_related('category').filter(category_id=category_id).order_by('-created_at', '-listing_id')

    return render(request, "marketplace/category_listings.html", {
        "page_title": f"{category.category_name} Listings",
        "selected_category": category,
        "listings": listings,
        "results_count": listings.count(),
    })


def edit_listing_view(request, listing_id):
    user = request.user
    if not request.user.is_authenticated:
        return redirect("login")

    market_user = request.user
    listing = get_object_or_404(Listing, listing_id=listing_id, seller=market_user)

    if request.method == "POST":
        # Handle delete action
        if request.POST.get("_action") == "delete":
            listing.delete()
            messages.success(request, "Listing deleted.")
            return redirect("account")

        listing.title = request.POST.get("title", listing.title).strip()
        listing.description = request.POST.get("description", listing.description).strip()
        listing.listing_type = request.POST.get("listing_type", listing.listing_type)
        listing.condition = request.POST.get("condition", listing.condition)
        main_picture_url = request.POST.get("main_picture_url", "").strip()
        # Handle uploaded image files — save all; first becomes the thumbnail
        uploaded_images = request.FILES.getlist("images")
        saved_image_urls = []
        for img_file in uploaded_images:
            url = _save_uploaded_image(img_file)
            if url:
                saved_image_urls.append(url)
        if saved_image_urls:
            main_picture_url = saved_image_urls[0]
        if main_picture_url:
            listing.main_picture_url = main_picture_url

        try:
            listing.price = round(float(request.POST.get("price", listing.price)), 2)
        except ValueError:
            pass

        try:
            cat = Category.objects.get(category_id=request.POST.get("category"))
            listing.category = cat
        except (Category.DoesNotExist, ValueError):
            pass

        if request.POST.get("clear_main_picture") == "1" and not main_picture_url:
            listing.main_picture_url = None
        listing.save()
        messages.success(request, "Listing updated!")
        return redirect("listing_detail", listing_id=listing.listing_id)

    context = base_context()
    context.update({
        "listing": listing,
        "user": user,
        "listing_types": ListingType.choices,
        "listing_intents": ListingIntent.choices,
        "conditions": CONDITION_CHOICES,
    })
    return render(request, "marketplace/edit_listing.html", context)


def listing_detail_view(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related("category", "seller"),
        listing_id=listing_id
    )
    market_user = request.user if request.user.is_authenticated else None
    context = base_context()
    context.update({
        "listing": listing,
        "user": request.user,
        "market_user": market_user,
    })
    return render(request, "marketplace/listing_detail.html", context)


# --- Dashboard/Account ---

def _get_past_listings(user):
    return Listing.objects.filter(seller=user).exclude(
        intent__in=LIVE_LISTING_INTENTS,
    ).exclude(
        intent=LEGACY_LIVE_LISTING_STATUS,
    ).order_by("-created_at")


def account_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    market_user = request.user
    unread_count = Message.objects.filter(receiver=market_user, is_read=False).count()
    
    user_listings = Listing.objects.filter(seller=market_user).order_by("-created_at")
    product_listings = user_listings.filter(listing_type="product")
    service_listings = user_listings.filter(listing_type="service")
    
    active_tab = request.GET.get("tab", "products")
    
    context = base_context()
    context.update({
        "user": request.user,
        "user_listings": user_listings,
        "unread_count": unread_count,
        "product_listings": product_listings,
        "service_listings": service_listings,
        "active_tab": active_tab,
    })
    return render(request, "marketplace/account.html", context)

# Public facing profile page
def profile_view(request, username):
    profile_user = get_object_or_404(User, username=username)
    market_user = get_marketplace_user(request.user) if request.user.is_authenticated else None
    
    user_listings = Listing.objects.filter(seller=profile_user).order_by("-created_at")
    product_listings = user_listings.filter(listing_type="product")
    service_listings = user_listings.filter(listing_type="service")
    
    active_tab = request.GET.get("tab", "products")

    context = base_context()
    context.update({
        "profile_user": profile_user,
        "market_user": market_user,
        "user_listings": user_listings,
        "product_listings": product_listings,
        "service_listings": service_listings,
        "active_tab": active_tab,
    })
    return render(request, "marketplace/profile.html", context)

def verify_student(request):
    context = base_context()
    return render(request, "marketplace/verify_student.html", context)


def edit_profile(request):
    context = base_context()
    if request.method == 'POST':
        # Update User model fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()

        # Update model fields
        profile = request.user.profile

        profile.avatar_url = request.POST.get('avatar_url', '')
        profile.year = request.POST.get('year', '')
        profile.major = request.POST.get('major', '')
        profile.bio = request.POST.get('bio', '')
        profile.save()
        return redirect('account')
    return render(request, "marketplace/edit_profile.html", context)

def past_listings(request):
    context = base_context()
    return render(request, "marketplace/past_listings.html", context)



# --- Messaging ---

def chat_view(request):
    if not request.user.is_authenticated:
        return redirect("login")

    market_user = request.user

    # Build threads grouped by (listing, other_user). This keeps chat scoped to listings.
    thread_map = {}
    message_qs = (
        Message.objects
        .filter(Q(sender=market_user) | Q(receiver=market_user), listing__isnull=False)
        .select_related("listing", "sender", "receiver")
        .order_by("created_at")
    )

    for msg in message_qs:
        other_user = msg.receiver if msg.sender_id == market_user.id else msg.sender
        key = (msg.listing_id, other_user.id)

        entry = thread_map.get(key)
        if entry is None:
            entry = {
                "listing": msg.listing,
                "other_user": other_user,
                "last_message": msg,
                "unread_count": 0,
            }
            thread_map[key] = entry

        # Track last message
        if msg.created_at >= entry["last_message"].created_at:
            entry["last_message"] = msg

        # Unread count for current user
        if msg.receiver_id == market_user.id and not msg.is_read:
            entry["unread_count"] += 1

    threads = sorted(
        thread_map.values(),
        key=lambda t: (t["last_message"].created_at, t["last_message"].message_id),
        reverse=True,
    )

    # Active thread selection
    active_listing_id = request.GET.get("listing")
    other_user_id = request.GET.get("with")
    conversation = []
    other_user = None
    active_listing = None

    if active_listing_id and other_user_id:
        try:
            active_listing = Listing.objects.select_related("seller").get(listing_id=int(active_listing_id))
            other_user = User.objects.get(id=int(other_user_id))

            # Only allow access to listing-scoped thread where the user is a participant
            is_valid_pair = (
                (market_user.id == active_listing.seller_id and other_user.id != active_listing.seller_id)
                or (market_user.id != active_listing.seller_id and other_user.id == active_listing.seller_id)
            )
            if not is_valid_pair:
                active_listing = None
                other_user = None
            else:
                conversation = (
                    Message.objects
                    .filter(
                        Q(sender=market_user, receiver=other_user) | Q(sender=other_user, receiver=market_user),
                        listing=active_listing,
                    )
                    .select_related("sender", "receiver")
                    .order_by("created_at")
                )
                conversation.filter(receiver=market_user, is_read=False).update(is_read=True)
        except (ValueError, Listing.DoesNotExist, User.DoesNotExist):
            active_listing = None
            other_user = None

    if request.method == "POST" and other_user and active_listing:
        content = (request.POST.get("content") or "").strip()
        if content:
            # Enforce: buyers initiate, sellers may reply only after a buyer message exists.
            if active_listing.seller_id == market_user.id:
                buyer_id = other_user.id
                if buyer_id == active_listing.seller_id:
                    messages.error(request, "Invalid conversation.")
                    return redirect("chat")

                buyer_initiated = Message.objects.filter(
                    listing=active_listing,
                    sender_id=buyer_id,
                    receiver_id=market_user.id,
                ).exists()
                if not buyer_initiated:
                    messages.error(request, "Only buyers can initiate a new chat about a listing.")
                    return redirect("chat")
            else:
                # Buyer can only message the listing's seller
                if other_user.id != active_listing.seller_id:
                    messages.error(request, "You can only message the seller for this listing.")
                    return redirect("chat")

            Message.objects.create(
                sender=market_user,
                receiver=other_user,
                listing=active_listing,
                content=content,
            )
            return redirect(f"/chat/?listing={active_listing.listing_id}&with={other_user.pk}")

    context = base_context()
    context.update({
        "user": market_user,
        "threads": threads,
        "conversation": conversation,
        "other_user": other_user,
        "active_listing": active_listing,
        "active_listing_id": int(active_listing_id) if (active_listing_id and str(active_listing_id).isdigit()) else None,
        "active_other_user_id": int(other_user_id) if (other_user_id and str(other_user_id).isdigit()) else None,
    })
    return render(request, "marketplace/chat.html", context)


@require_GET
def chat_poll_view(request):
    """Return new messages for the active listing-scoped thread.

    Query params:
      - listing: listing_id
      - with: other user's id
      - after_id: last message_id currently on the page
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth_required"}, status=401)

    market_user = request.user

    raw_listing_id = request.GET.get("listing")
    raw_other_user_id = request.GET.get("with")
    raw_after_id = request.GET.get("after_id")

    try:
        listing_id = int(raw_listing_id)
        other_user_id = int(raw_other_user_id)
    except (TypeError, ValueError):
        return JsonResponse({"error": "invalid_params"}, status=400)

    after_id = 0
    try:
        if raw_after_id:
            after_id = int(raw_after_id)
    except (TypeError, ValueError):
        after_id = 0

    listing = get_object_or_404(Listing, listing_id=listing_id)
    other_user = get_object_or_404(User, id=other_user_id)

    # Must be part of this listing chat
    is_valid_pair = (
        (market_user.id == listing.seller_id and other_user.id != listing.seller_id)
        or (market_user.id != listing.seller_id and other_user.id == listing.seller_id)
    )
    if not is_valid_pair:
        return JsonResponse({"error": "forbidden"}, status=403)

    new_messages = (
        Message.objects
        .filter(
            Q(sender=market_user, receiver=other_user) | Q(sender=other_user, receiver=market_user),
            listing=listing,
            message_id__gt=after_id,
        )
        .select_related("sender", "receiver")
        .order_by("created_at")[:50]
    )

    # Mark newly fetched incoming messages as read
    Message.objects.filter(
        message_id__in=[m.message_id for m in new_messages if m.receiver_id == market_user.id and not m.is_read]
    ).update(is_read=True)

    payload = {
        "messages": [
            {
                "id": m.message_id,
                "sender_id": m.sender_id,
                "content": m.content,
                "created_at": timezone.localtime(m.created_at).isoformat(),
                "created_at_display": timezone.localtime(m.created_at).strftime("%b %d, %I:%M %p"),
                "is_outgoing": m.sender_id == market_user.id,
            }
            for m in new_messages
        ]
    }

    return JsonResponse(payload)


@require_GET
def chat_threads_poll_view(request):
    """Return listing-scoped thread summaries for the logged-in user.

    Used by the chat sidebar to refresh unread badges/timestamps.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth_required"}, status=401)

    market_user = request.user

    thread_map = {}
    message_qs = (
        Message.objects
        .filter(Q(sender=market_user) | Q(receiver=market_user), listing__isnull=False)
        .select_related("listing", "sender", "receiver")
        .order_by("created_at")
    )

    for msg in message_qs:
        other_user = msg.receiver if msg.sender_id == market_user.id else msg.sender
        key = (msg.listing_id, other_user.id)

        entry = thread_map.get(key)
        if entry is None:
            entry = {
                "listing": msg.listing,
                "other_user": other_user,
                "last_message": msg,
                "unread_count": 0,
            }
            thread_map[key] = entry

        if msg.created_at >= entry["last_message"].created_at:
            entry["last_message"] = msg

        if msg.receiver_id == market_user.id and not msg.is_read:
            entry["unread_count"] += 1

    threads = sorted(
        thread_map.values(),
        key=lambda t: (t["last_message"].created_at, t["last_message"].message_id),
        reverse=True,
    )

    payload = {
        "threads": [
            {
                "listing_id": t["listing"].listing_id,
                "listing_title": t["listing"].title,
                "other_user_id": t["other_user"].id,
                "other_user_name": (t["other_user"].get_full_name() or t["other_user"].username),
                "last_message_id": t["last_message"].message_id,
                "last_message_content": t["last_message"].content,
                "last_message_created_at": timezone.localtime(t["last_message"].created_at).isoformat(),
                "last_message_created_at_display": timezone.localtime(t["last_message"].created_at).strftime("%b %d, %I:%M %p"),
                "unread_count": t["unread_count"],
            }
            for t in threads
        ]
    }

    return JsonResponse(payload)


def send_message_view(request, listing_id):
    """Start a conversation about a listing (from listing detail page)."""
    if not request.user.is_authenticated:
        return redirect("login")

    listing = get_object_or_404(Listing, listing_id=listing_id)
    market_user = request.user

    chat_url = f"{reverse('chat')}?listing={listing.listing_id}&with={listing.seller_id}"

    # Seller cannot start a conversation about their own listing.
    if listing.seller_id == market_user.id:
        return redirect("listing_detail", listing_id=listing_id)

    if request.method == "POST":
        content = (request.POST.get("content") or "").strip()
        if content:
            Message.objects.create(
                sender=market_user,
                receiver=listing.seller,
                listing=listing,
                content=content,
            )
            messages.success(request, "Message sent!")

    # Always land user in the listing-scoped chat thread.
    return redirect(chat_url)