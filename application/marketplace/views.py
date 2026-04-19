# application/marketplace/views.py
# View functions for the marketplace app.
# Created by Subreet Singh on 04-09-2026

from decimal import Decimal, InvalidOperation

from django.shortcuts import render, get_object_or_404, redirect, render
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from backend.models import Category, Listing, ListingIntent, ListingType, User, Role, Message



def base_context():
    return {
        "categories": Category.objects.all().order_by("category_name"),
    }


def _get_logged_in_user(request):
    """Return the User object stored in session, or None."""
    user_id = request.session.get("user_id")
    if user_id:
        try:
            return User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            request.session.flush()
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
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")

        try:
            user = User.objects.get(sfsu_email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return render(request, "marketplace/login.html", base_context())

        if not user.check_password(password):
            messages.error(request, "Invalid email or password.")
            return render(request, "marketplace/login.html", base_context())

        if user.account_status != "active":
            messages.error(request, "Your account is not active.")
            return render(request, "marketplace/login.html", base_context())

        # Store user in session
        request.session["user_id"] = user.user_id
        request.session["user_email"] = user.sfsu_email
        request.session["user_name"] = f"{user.first_name} {user.last_name}"
        return redirect("marketplace_home")

    return render(request, "marketplace/login.html", base_context())


def register_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")

        # Validate SFSU email
        if not email.endswith("@sfsu.edu"):
            messages.error(request, "You must use an @sfsu.edu email address.")
            return render(request, "marketplace/register.html", base_context())

        if not first_name or not last_name:
            messages.error(request, "First and last name are required.")
            return render(request, "marketplace/register.html", base_context())

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters.")
            return render(request, "marketplace/register.html", base_context())

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, "marketplace/register.html", base_context())

        if User.objects.filter(sfsu_email=email).exists():
            messages.error(request, "An account with this email already exists.")
            return render(request, "marketplace/register.html", base_context())

        # Create the user
        student_role, _ = Role.objects.get_or_create(role_name="student")
        user = User(
            sfsu_email=email,
            first_name=first_name,
            last_name=last_name,
            role=student_role,
            account_status="active",
        )
        user.set_password(password)
        user.save()

        # Auto-login after registration
        request.session["user_id"] = user.user_id
        request.session["user_email"] = user.sfsu_email
        request.session["user_name"] = f"{user.first_name} {user.last_name}"
        messages.success(request, "Account created successfully!")
        return redirect("marketplace_home")


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
    request.session.flush()
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
        "user": _get_logged_in_user(request),
        "intent": intent,
        "selected_category_ids": [str(category_id) for category_id in selected_category_ids],
        "price_min": price_min,
        "price_max": price_max,
    })


# --- Listing CRUD ---

def create_listing_view(request):
    user = _get_logged_in_user(request)
    if not user:
        messages.error(request, "You must be logged in to create a listing.")
        return redirect("login")

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        price = request.POST.get("price", "0")
        listing_type = request.POST.get("listing_type", "product")
        condition = request.POST.get("condition", "Good")
        category_id = request.POST.get("category", "")
        thumbnail_url = request.POST.get("thumbnail_url", "").strip()

        if not title:
            messages.error(request, "Title is required.")
            context = base_context()
            context["user"] = user
            return render(request, "marketplace/create_listing.html", context)

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
            status="active",
            thumbnail_url=thumbnail_url or None,
        )
        messages.success(request, "Listing created!")
        return redirect("listing_detail", listing_id=listing.listing_id)

    context = base_context()
    context["user"] = user
    return render(request, "marketplace/create_listing.html", context)


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
    user = _get_logged_in_user(request)
    if not user:
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
    context.update({"listing": listing, "user": user})
    return render(request, "marketplace/edit_listing.html", context)


def listing_detail_view(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related("category", "seller"),
        listing_id=listing_id
    )
    context = base_context()
    context.update({
        "listing": listing,
        "user": _get_logged_in_user(request),
    })
    return render(request, "marketplace/listing_detail.html", context)


# --- Dashboard/Account ---

def account_view(request):
    user = _get_logged_in_user(request)
    if not user:
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


# --- Messaging ---

def chat_view(request):
    user = _get_logged_in_user(request)
    if not user:
        return redirect("login")

    # Get all conversations (unique users this user has messaged with)
    sent = Message.objects.filter(sender=user).values_list("receiver_id", flat=True)
    received = Message.objects.filter(receiver=user).values_list("sender_id", flat=True)
    contact_ids = set(list(sent) + list(received))
    contacts = User.objects.filter(user_id__in=contact_ids)

    # If a specific conversation is selected
    other_user_id = request.GET.get("with")
    conversation = []
    other_user = None

    if other_user_id:
        try:
            other_user = User.objects.get(user_id=other_user_id)
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
            return redirect(f"/chat/?with={other_user.user_id}")

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
    user = _get_logged_in_user(request)
    if not user:
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