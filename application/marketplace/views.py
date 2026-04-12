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
        "title": "Desk Lamp",
        "price": "$15",
        "category": "Furniture",
        "posted": "30 minutes ago",
        "image": "images/marketplace/placeholder-listing.svg",
    },
    {
        "title": "Bike Lock",
        "price": "$10",
        "category": "Other",
        "posted": "1 hour ago",
        "image": "images/marketplace/placeholder-listing.svg",
    },
    {
        "title": "Graphic Design Help",
        "price": "$25",
        "category": "Services",
        "posted": "2 hours ago",
        "image": "images/marketplace/placeholder-listing.svg",
    },
    {
        "title": "Headphones",
        "price": "$40",
        "category": "Electronics",
        "posted": "6 hours ago",
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
    query = request.GET.get("query", None) or "All"
    results = RECENT_LISTINGS # TODO - fetch from BE
    
    return render(request, "marketplace/search_results.html", dict(
        page_title="Results for %s" % query,
        results=results,
        query=query
    ))


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