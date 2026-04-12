# pages/urls.py
## This file defines the URL patterns for the "pages" app. It maps URL paths to view functions that handle the requests and return responses.
### Django imports
### Created by Subreet Singh on 02-23-2026

from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("", views.about, name="about"),
    path("team/<slug:slug>/", views.member_detail, name="member_detail"),
]