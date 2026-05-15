from django.test import TestCase
from django.urls import reverse

from backend.models import Category, Listing, ListingIntent, ListingType, Role, User


class AccountListingsViewTests(TestCase):
    def setUp(self):
        self.role = Role.objects.create(role_name="student")
        self.user = User.objects.create(
            sfsu_email="owner@sfsu.edu",
            first_name="Owner",
            last_name="User",
            role=self.role,
            password_hash="hashed",
            account_status="active",
        )
        self.other_user = User.objects.create(
            sfsu_email="other@sfsu.edu",
            first_name="Other",
            last_name="User",
            role=self.role,
            password_hash="hashed",
            account_status="active",
        )
        self.category = Category.objects.create(
            category_name="Textbooks",
            category_description="Books",
        )

        self.active_listing = Listing.objects.create(
            title="Active Listing",
            description="Still live",
            price="10.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.user,
        )
        self.past_listing = Listing.objects.create(
            title="Past Listing",
            description="Already sold",
            price="12.00",
            listing_type=ListingType.PRODUCT,
            intent="sold",
            condition="Good",
            category=self.category,
            seller=self.user,
        )
        Listing.objects.create(
            title="Other User Listing",
            description="Should not appear",
            price="8.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Fair",
            category=self.category,
            seller=self.other_user,
        )

    def _login(self):
        session = self.client.session
        session["user_id"] = self.user.user_id
        session.save()

    def test_account_view_shows_active_tab_by_default(self):
        self._login()

        response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "active")
        self.assertIn(self.active_listing, response.context["user_listings"])
        self.assertIn(self.past_listing, response.context["user_listings"])
        self.assertEqual(list(response.context["past_listings"]), [self.past_listing])

    def test_account_view_supports_past_tab_query_param(self):
        self._login()

        response = self.client.get(reverse("account"), {"tab": "past"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "past")
        self.assertContains(response, "Past Listings")
        self.assertContains(response, self.past_listing.title)

    def test_past_listings_route_shows_only_past_for_logged_in_user(self):
        self._login()

        response = self.client.get(reverse("past_listings"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["active_tab"], "past")
        self.assertEqual(list(response.context["past_listings"]), [self.past_listing])
        self.assertNotIn(self.active_listing, response.context["past_listings"])

    def test_account_and_past_routes_require_login(self):
        account_response = self.client.get(reverse("account"))
        past_response = self.client.get(reverse("past_listings"))

        self.assertEqual(account_response.status_code, 302)
        self.assertEqual(past_response.status_code, 302)
        self.assertIn(reverse("login"), account_response.url)
        self.assertIn(reverse("login"), past_response.url)
