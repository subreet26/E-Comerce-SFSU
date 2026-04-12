from backend.models import Category


def marketplace_categories(request):
    categories = [
        {
            'id': category.category_id,
            'name': category.category_name,
            'description': category.category_description,
        }
        for category in Category.objects.order_by('category_name')
    ]
    return {'categories': categories}