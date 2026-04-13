from .views import CATEGORIES


def marketplace_globals(request):
    return {
        "categories": CATEGORIES,
        "query": (request.GET.get("q") or request.GET.get("query") or "").strip(),
    }