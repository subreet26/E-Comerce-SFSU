from .models import Category, Message

def marketplace_globals(request):
    categories = Category.objects.order_by('category_name')

    unread_count = 0
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        unread_count = Message.objects.filter(receiver=request.user, is_read=False).count()

    return {
        'categories': categories,
        "query": (request.GET.get("q") or request.GET.get("query") or "").strip(),
        "unread_count": unread_count,
    }

