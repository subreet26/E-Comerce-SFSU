# application/marketplace/views.py
## This file defines the view functions for the "marketplace" app. These functions handle incoming HTTP
## requests related to the marketplace, process any necessary data, and return HTTP responses, often by
## Created by Subreet Singh on 04-09-2026

from django.shortcuts import render

CATEGORIES = [
    {"name": "Textbooks", "icon": "📚"},
    {"name": "Electronics", "icon": "💻"},
    {"name": "Furniture", "icon": "🪑"},
    {"name": "Clothing", "icon": "👕"},
    {"name": "Services", "icon": "🛠️"},
    {"name": "Other", "icon": "📦"},
]

def base_context():
    return {
        "categories": CATEGORIES,
    }

FEATURED_LISTINGS = [

]

RECENT_LISTINGS = [
    {
        "id": 1,
        "title": "Desk Lamp",
        "price": "$15",
        "listing_type": "product",
        "intent": "offered",
        "category": "Furniture",
        "posted": "30 minutes ago",
        "posted_order": 1,
        "image": "images/marketplace/placeholder-listing.svg",
    },
    {
        "id": 2,
        "title": "Bike Lock",
        "price": "$10",
        "listing_type": "product",
        "intent": "wanted",
        "category": "Other",
        "posted": "1 hour ago",
        "posted_order": 2,
        "image": "images/marketplace/placeholder-listing.svg",
    },
    {
        "id": 3,
        "title": "Graphic Design Help",
        "price": "$25",
        "listing_type": "service",
        "intent": "offered",
        "category": "Services",
        "posted": "2 hours ago",
        "posted_order": 3,
        "image": "images/marketplace/placeholder-listing.svg",
    },
    {
        "id": 4,
        "title": "Headphones",
        "price": "$40",
        "listing_type": "product",
        "intent": "offered",
        "category": "Electronics",
        "posted": "6 hours ago",
        "posted_order": 4,
        "image": "images/marketplace/placeholder-listing.svg",
    },
]


def marketplace_home(request):
    context = {
        "categories": CATEGORIES,
        "featured_listings": FEATURED_LISTINGS,
        "recent_listings": RECENT_LISTINGS,
    }
    return render(request, "marketplace/home.html", context)


# Additional view functions for login, registration, listing details, etc. would go here.
# For example:
# def login_view(request):
#    return render(request, "marketplace/login.html")
# i did add placeholders for now 

def login_view(request):
    return render(request, "marketplace/login.html")


def register_view(request):
    return render(request, "marketplace/register.html")


def search_results_view(request):
    query = (request.GET.get("q") or request.GET.get("query") or "").strip()
    listing_type = (request.GET.get("type") or "all").strip().lower()
    date_order = (request.GET.get("date") or "newest").strip().lower()
    intent = (request.GET.get("intent") or "all").strip().lower()

    results = list(RECENT_LISTINGS)  # TODO - fetch from BE

    if query:
        query_lower = query.lower()
        results = [
            listing for listing in results
            if query_lower in listing.get("title", "").lower()
            or query_lower in listing.get("category", "").lower()
        ]

    if listing_type in {"product", "service"}:
        results = [
            listing for listing in results
            if listing.get("listing_type") == listing_type
        ]

    if intent in {"offered", "wanted"}:
        results = [
            listing for listing in results
            if listing.get("intent") == intent
        ]

    if date_order == "oldest":
        results.sort(key=lambda listing: listing.get("posted_order", 0), reverse=True)
    else:
        date_order = "newest"
        results.sort(key=lambda listing: listing.get("posted_order", 0))

    return render(request, "marketplace/search_results.html", {
        "page_title": f"Results for {query}" if query else "Search Results",
        "results": results,
        "query": query,
        "listing_type": listing_type if listing_type in {"all", "product", "service"} else "all",
        "date_order": date_order,
        "intent": intent if intent in {"all", "offered", "wanted"} else "all",
        "results_count": len(results),
    })


def account_view(request):
    return render(request, "marketplace/account.html")


def create_listing_view(request):
    return render(request, "marketplace/create_listing.html")


def edit_listing_view(request, listing_id):
    return render(request, "marketplace/edit_listing.html", {"listing_id": listing_id})


def listing_detail_view(request, listing_id):
    return render(request, "marketplace/listing_detail.html", {"listing_id": listing_id})


def chat_view(request):
    return render(request, "marketplace/chat.html")