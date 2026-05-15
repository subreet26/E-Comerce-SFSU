from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class AccountViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="michal",
            email="michal@krupanet.org",
            sfsu_email="michal@krupanet.org",
            password="pass1234",
        )

    def test_account_page_does_not_sync_marketplace_user_on_get(self):
        self.client.force_login(self.user)

        with patch("marketplace.views.get_marketplace_user", side_effect=AssertionError("should not be called")):
            response = self.client.get(reverse("account"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Account")
