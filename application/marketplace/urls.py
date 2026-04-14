from django.urls import path
from . import views

urlpatterns = [
    path("", views.marketplace_home, name="marketplace_home"),
    path("categories/<int:category_id>/", views.category_listings_view, name="category_listings"),
    path("login/", views.login_view, name="login"),
    path("register/", views.register_view, name="register"),
    path("logout/", views.logout_view, name="logout"),
    path("search/", views.search_results_view, name="search_results"),
    path("account/", views.account_view, name="account"),
    path("listings/new/", views.create_listing_view, name="create_listing"),
    path("listings/<int:listing_id>/edit/", views.edit_listing_view, name="edit_listing"),
    path("listings/<int:listing_id>/", views.listing_detail_view, name="listing_detail"),
    path("listings/<int:listing_id>/message/", views.send_message_view, name="send_message"),
    path("chat/", views.chat_view, name="chat"),
]