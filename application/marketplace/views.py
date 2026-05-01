# application/marketplace/views.py
# View functions for the marketplace app.
# Created by Subreet Singh on 04-09-2026

from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth import get_user_model
from .models import Category, Listing, ListingIntent, ListingType, Message
from .forms import RegisterForm


User = get_user_model()

CONDITION_CHOICES = [
    ("new", "New"),
    ("like_new", "Like New"),
    ("good", "Good"),
    ("fair", "Fair"),
    ("poor", "Poor"),
]


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
    if request.method == "POST":
        username_or_email = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username_or_email or not password:
            messages.error(request, "Please enter both username/email and password.")
            return render(request, "marketplace/login.html")

        # Check if user exists (by username or email)
        user_exists = User.objects.filter(
            Q(username=username_or_email) | Q(email__iexact=username_or_email)
        ).exists()

        if not user_exists:
            messages.error(request, "Username or email not found.")
            return render(request, "marketplace/login.html")

        # Attempt authentication with custom backend
        user = authenticate(request, username=username_or_email, password=password)

        if user is not None:
            login(request, user)
            return redirect(request.GET.get("next") or "marketplace_home")
        else:
            # User exists but password is incorrect
            messages.error(request, "Incorrect password.")

    return render(request, "marketplace/login.html")


def register_view(request):
    """
    Handle user registration with comprehensive backend validation.
    Validates username, email (@sfsu.edu domain), and password requirements.
    Password is hashed using Django's default PBKDF2 hasher.
    Auto-logs in user after successful registration.
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            # Save user with hashed password
            user = form.save(commit=True)

            # Auto-login after registration
            login(request, user)
            messages.success(request, "Account created successfully!")

            return redirect("marketplace_home")
        else:
            # Form validation errors will be displayed in template
            # Errors from RegisterForm include: username uniqueness, email domain, password strength
            pass

    else:
        form = RegisterForm()

    return render(request, "marketplace/register.html", {
        "form": form
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

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "0")
        listing_type = request.POST.get("listing_type", ListingType.PRODUCT)
        status = request.POST.get("status", "active")
        condition = request.POST.get("condition", "good")
        category_id = request.POST.get("category", "")
        thumbnail_url = request.POST.get("thumbnail_url", "").strip()

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
            seller=user,
            intent=status,
            thumbnail_url=thumbnail_url or None,
        )
        listing.save()
        messages.success(request, "Listing created!")
        return redirect("listing_detail", listing_id=listing.listing_id)

    context = base_context()
    context["user"] = user
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

    listing = get_object_or_404(Listing, listing_id=listing_id, seller=user)

    if request.method == "POST":
        listing.title = request.POST.get("title", listing.title).strip()
        listing.description = request.POST.get("description", listing.description).strip()
        listing.listing_type = request.POST.get("listing_type", listing.listing_type)
        listing.condition = request.POST.get("condition", listing.condition)
        thumbnail_url = request.POST.get("thumbnail_url", "").strip()
        if thumbnail_url:
            listing.thumbnail_url = thumbnail_url

        try:
            listing.price = round(float(request.POST.get("price", listing.price)), 2)
        except ValueError:
            pass

        try:
            cat = Category.objects.get(category_id=request.POST.get("category"))
            listing.category = cat
        except (Category.DoesNotExist, ValueError):
            pass

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
    context = base_context()
    context.update({
        "listing": listing,
        "user": request.user,
    })
    return render(request, "marketplace/listing_detail.html", context)


# --- Dashboard/Account ---

def account_view(request):
    user = request.user
    if not request.user.is_authenticated:
        return redirect("login")

    user_listings = Listing.objects.filter(seller=user).order_by("-created_at")
    unread_count = Message.objects.filter(receiver=user, is_read=False).count()

    context = base_context()
    context.update({
        "user": user,
        "user_listings": user_listings,
        "unread_count": unread_count,
    })
    return render(request, "marketplace/account.html", context)

def verify_student(request):
    pass

def edit_profile(request):
    pass


# --- Messaging ---

def chat_view(request):
    user = request.user
    if not request.user.is_authenticated:
        return redirect("login")

    # Get all conversations (unique users this user has messaged with)
    sent = Message.objects.filter(sender=user).values_list("receiver_id", flat=True)
    received = Message.objects.filter(receiver=user).values_list("sender_id", flat=True)
    contact_ids = set(list(sent) + list(received))
    contacts = User.objects.filter(id__in=contact_ids)

    # If a specific conversation is selected
    other_user_id = request.GET.get("with")
    conversation = []
    other_user = None

    if other_user_id:
        try:
            other_user = User.objects.get(id=other_user_id)
            conversation = Message.objects.filter(
                (Q(sender=user, receiver=other_user) | Q(sender=other_user, receiver=user))
            ).order_by("created_at")
            # Mark messages as read
            conversation.filter(receiver=user, is_read=False).update(is_read=True)
        except User.DoesNotExist:
            pass

    if request.method == "POST" and other_user:
        content = request.POST.get("content", "").strip()
        listing_id = request.POST.get("listing_id")
        if content:
            msg = Message(sender=user, receiver=other_user, content=content)
            if listing_id:
                try:
                    msg.listing = Listing.objects.get(listing_id=listing_id)
                except Listing.DoesNotExist:
                    pass
            msg.save()
            return redirect(f"/chat/?with={other_user.id}")

    context = base_context()
    context.update({
        "user": user,
        "contacts": contacts,
        "conversation": conversation,
        "other_user": other_user,
    })
    return render(request, "marketplace/chat.html", context)


def send_message_view(request, listing_id):
    """Start a conversation about a listing (from listing detail page)."""
    user = request.user
    if not request.user.is_authenticated:
        return redirect("login")

    listing = get_object_or_404(Listing, listing_id=listing_id)

    if request.method == "POST":
        content = request.POST.get("content", "").strip()
        if content and listing.seller != user:
            Message.objects.create(
                sender=user,
                receiver=listing.seller,
                listing=listing,
                content=content,
            )
            messages.success(request, "Message sent!")
    return redirect("listing_detail", listing_id=listing_id)