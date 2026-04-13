# application/marketplace/views.py
## This file defines the view functions for the "marketplace" app. These functions handle incoming HTTP
## requests related to the marketplace, process any necessary data, and return HTTP responses, often by
## Created by Subreet Singh on 04-09-2026

from django.shortcuts import render, get_object_or_404
from backend.models import Category, Listing

def base_context():
    return {
        "categories": Category.objects.all().order_by("category_name"),
    }


def marketplace_home(request):
    context = base_context()
    context.update({
        "recent_listings": Listing.objects.select_related("category", "seller").order_by("-created_at")[:8],
    })
    return render(request, "marketplace/home.html", context)

# Additional view functions for login, registration, listing details, etc. would go here.
# For example:
# def login_view(request):
#    return render(request, "marketplace/login.html")
# i did add placeholders for now 

def login_view(request):
    return render(request, "marketplace/login.html", base_context())


def register_view(request):
    return render(request, "marketplace/register.html", base_context())


def search_results_view(request):
    from django.core.paginator import Paginator
    from django.db.models import Q
    from backend.models import Listing, Category

    query        = (request.GET.get("q") or request.GET.get("query") or "").strip()
    listing_type = (request.GET.get("type") or "all").strip().lower()
    date_order   = (request.GET.get("date") or "newest").strip().lower()
    intent       = (request.GET.get("intent") or "all").strip().lower()
    category     = (request.GET.get("category") or "all").strip()

    # SQL query via Django ORM — %LIKE on title + description (per M2 spec)
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

    db_categories = [{"name": c.category_name} for c in Category.objects.all()]

    return render(request, "marketplace/search_results.html", {
        "page_title": f"Results for {query}" if query else "Search Results",
        "results": page_obj,
        "page_obj": page_obj,
        "query": query,
        "listing_type": listing_type if listing_type in {"all", "product", "service"} else "all",
        "date_order": date_order,
        "intent": intent if intent in {"all", "offered", "wanted"} else "all",
        "category": category,
        "categories": db_categories,
        "results_count": total_count,
    })


def account_view(request):
    return render(request, "marketplace/account.html", base_context())


def create_listing_view(request):
    return render(request, "marketplace/create_listing.html", base_context())


def edit_listing_view(request, listing_id):
    context = base_context()
    context.update({"listing_id": listing_id})
    return render(request, "marketplace/edit_listing.html", context)


def listing_detail_view(request, listing_id):
    listing = get_object_or_404(
        Listing.objects.select_related("category", "seller"),
        listing_id=listing_id
    )
    context = base_context()
    context.update({"listing": listing})
    return render(request, "marketplace/listing_detail.html", context)


def chat_view(request):
    return render(request, "marketplace/chat.html", base_context())