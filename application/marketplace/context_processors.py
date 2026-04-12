from backend.models import Category

from .views import CATEGORIES


def marketplace_globals(request):
    categories = [
        {
            'id': category.category_id,
            'name': category.category_name,
            'description': category.category_description,
        }
        for category in Category.objects.order_by('category_name')
    ]
    return {
        'categories': categories,
        "query": (request.GET.get("q") or request.GET.get("query") or "").strip(),
    }

