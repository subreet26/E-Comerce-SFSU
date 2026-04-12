from decimal import Decimal, InvalidOperation

from django.db.models import Q
from django.shortcuts import get_object_or_404, render

from backend.models import Category, Listing, ListingIntent, ListingType


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


def marketplace_home(request):
    recent_listings = Listing.objects.select_related('category').order_by('-created_at')[:4]
    context = _marketplace_context(
        recent_listings=recent_listings,
    )
    return render(request, "marketplace/home.html", context)


def login_view(request):
    return render(request, "marketplace/login.html", _marketplace_context())


def register_view(request):
    return render(request, "marketplace/register.html", _marketplace_context())


def search_results_view(request):
    query = (request.GET.get("q") or request.GET.get("query") or "").strip()
    listing_type = (request.GET.get("type") or "all").strip().lower()
    date_order = (request.GET.get("date") or "newest").strip().lower()
    intent = (request.GET.get("intent") or "all").strip().lower()
    selected_category_ids = _parse_category_ids(request.GET.getlist("categories"))
    price_min = _parse_decimal(request.GET.get("price_min"))
    price_max = _parse_decimal(request.GET.get("price_max"))

    results = Listing.objects.select_related('category').all()

    if query:
        results = results.filter(
            Q(name__icontains=query)
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
        "results": results,
        "query": query,
        "listing_type": listing_type,
        "date_order": date_order,
        "intent": intent,
        "selected_category_ids": [str(category_id) for category_id in selected_category_ids],
        "price_min": price_min,
        "price_max": price_max,
        "results_count": results.count(),
    })


def category_listings_view(request, category_id):
    category = get_object_or_404(Category, pk=category_id)
    listings = Listing.objects.select_related('category').filter(category_id=category_id).order_by('-created_at', '-listing_id')

    return render(request, "marketplace/category_listings.html", {
        "page_title": f"{category.category_name} Listings",
        "selected_category": category,
        "listings": listings,
        "results_count": listings.count(),
    })


def account_view(request):
    return render(request, "marketplace/account.html", _marketplace_context())


def create_listing_view(request):
    return render(request, "marketplace/create_listing.html", _marketplace_context())


def edit_listing_view(request, listing_id):
    return render(request, "marketplace/edit_listing.html", {"listing_id": listing_id})


def listing_detail_view(request, listing_id):
    return render(request, "marketplace/listing_detail.html", {"listing_id": listing_id})


def chat_view(request):
    return render(request, "marketplace/chat.html", _marketplace_context())