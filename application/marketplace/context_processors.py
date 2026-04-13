from backend.models import Category


def marketplace_globals(request):
    return {
        "categories": Category.objects.all().order_by("category_name"),
        "query": (request.GET.get("q") or request.GET.get("query") or "").strip(),
    }
