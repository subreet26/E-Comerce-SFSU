from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from marketplace.models import ApprovalStatus, Category, Listing, ListingIntent, ListingType, Role

User = get_user_model()


class AdminApprovalTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.student_role = Role.objects.create(role_name="student")
        self.admin_role = Role.objects.create(role_name="admin")

        self.seller = User.objects.create_user(
            username="seller1",
            email="seller1@sfsu.edu",
            sfsu_email="seller1@sfsu.edu",
            password="pass1234",
            role=self.student_role,
            password_hash="hashed",
        )
        self.admin = User.objects.create_user(
            username="admin1",
            email="admin1@sfsu.edu",
            sfsu_email="admin1@sfsu.edu",
            password="pass1234",
            role=self.admin_role,
            password_hash="hashed",
            is_staff=True,
        )
        self.other = User.objects.create_user(
            username="other1",
            email="other1@sfsu.edu",
            sfsu_email="other1@sfsu.edu",
            password="pass1234",
            role=self.student_role,
            password_hash="hashed",
        )
        self.category = Category.objects.create(
            category_name="Textbooks",
            category_description="Books",
        )
        self.approved_listing = Listing.objects.create(
            title="Approved Listing",
            description="Visible",
            price="10.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.APPROVED,
        )
        self.pending_listing = Listing.objects.create(
            title="Pending Listing",
            description="Hidden",
            price="15.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.PENDING,
        )

    def test_pending_listing_not_on_home(self):
        response = self.client.get(reverse("marketplace_home"))
        self.assertEqual(response.status_code, 200)
        recent = list(response.context["recent_listings"])
        self.assertIn(self.approved_listing, recent)
        self.assertNotIn(self.pending_listing, recent)

    def test_pending_listing_not_in_search(self):
        response = self.client.get(reverse("search_results"), {"q": "Listing"})
        self.assertEqual(response.status_code, 200)
        result_ids = {listing.listing_id for listing in response.context["page_obj"]}
        self.assertIn(self.approved_listing.listing_id, result_ids)
        self.assertNotIn(self.pending_listing.listing_id, result_ids)

    def test_pending_listing_not_in_category(self):
        response = self.client.get(
            reverse("category_listings", kwargs={"category_id": self.category.category_id}),
        )
        self.assertEqual(response.status_code, 200)
        listing_ids = {listing.listing_id for listing in response.context["listings"]}
        self.assertIn(self.approved_listing.listing_id, listing_ids)
        self.assertNotIn(self.pending_listing.listing_id, listing_ids)

    def test_listing_detail_404_for_anonymous_pending(self):
        response = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 404)

    def test_listing_detail_200_for_owner_pending(self):
        self.client.force_login(self.seller)
        response = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 200)

    def test_listing_detail_200_for_admin_pending(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 200)

    def test_account_shows_pending_queue_for_admin(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_admin"])
        queue_ids = {listing.listing_id for listing in response.context["pending_listings"]}
        self.assertIn(self.pending_listing.listing_id, queue_ids)
        self.assertContains(response, self.pending_listing.title)
        self.assertContains(response, "Pending Approvals")

    def test_account_hides_pending_queue_for_non_admin(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_admin"])
        self.assertEqual(list(response.context["pending_listings"]), [])
        self.assertNotContains(response, "Pending Approvals")

    def test_admin_approve_listing(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_approve_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 302)
        self.pending_listing.refresh_from_db()
        self.assertEqual(self.pending_listing.approval_status, ApprovalStatus.APPROVED)
        self.assertEqual(self.pending_listing.approved_by, self.admin)
        self.assertIsNotNone(self.pending_listing.approved_at)

        search_response = self.client.get(reverse("search_results"), {"q": "Pending"})
        result_ids = {listing.listing_id for listing in search_response.context["page_obj"]}
        self.assertIn(self.pending_listing.listing_id, result_ids)

    def test_admin_reject_listing(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_reject_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
            {"rejection_reason": "Incomplete description"},
        )
        self.assertEqual(response.status_code, 302)
        self.pending_listing.refresh_from_db()
        self.assertEqual(self.pending_listing.approval_status, ApprovalStatus.REJECTED)
        self.assertEqual(self.pending_listing.rejection_reason, "Incomplete description")

    # --- additional coverage ---

    def test_new_listing_defaults_to_pending(self):
        listing = Listing.objects.create(
            title="Fresh Listing",
            description="No status passed",
            price="20.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
        )
        self.assertEqual(listing.approval_status, ApprovalStatus.PENDING)

    def test_create_listing_submits_as_pending(self):
        self.client.force_login(self.seller)
        response = self.client.post(
            reverse("create_listing"),
            {
                "title": "Newly Submitted",
                "description": "Submitted via form",
                "price": "9.99",
                "listing_type": ListingType.PRODUCT,
                "status": ListingIntent.FOR_SALE,
                "condition": "good",
                "category": str(self.category.category_id),
            },
        )
        self.assertEqual(response.status_code, 302)
        created = Listing.objects.get(title="Newly Submitted")
        self.assertEqual(created.approval_status, ApprovalStatus.PENDING)
        self.assertEqual(created.seller, self.seller)

        home = self.client.get(reverse("marketplace_home"))
        recent_ids = {listing.listing_id for listing in home.context["recent_listings"]}
        self.assertNotIn(created.listing_id, recent_ids)

    def test_pending_service_listing_also_hidden(self):
        pending_service = Listing.objects.create(
            title="Pending Service",
            description="Tutoring",
            price="25.00",
            listing_type=ListingType.SERVICE,
            intent=ListingIntent.FOR_SALE,
            condition="N/A",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.PENDING,
        )
        response = self.client.get(reverse("search_results"), {"q": "Service"})
        result_ids = {listing.listing_id for listing in response.context["page_obj"]}
        self.assertNotIn(pending_service.listing_id, result_ids)

    def test_rejected_listing_hidden_from_public(self):
        rejected = Listing.objects.create(
            title="Rejected Listing",
            description="Not allowed",
            price="5.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.REJECTED,
        )
        search = self.client.get(reverse("search_results"), {"q": "Rejected"})
        result_ids = {listing.listing_id for listing in search.context["page_obj"]}
        self.assertNotIn(rejected.listing_id, result_ids)

        detail = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": rejected.listing_id}),
        )
        self.assertEqual(detail.status_code, 404)

    def test_rejected_listing_visible_to_owner(self):
        rejected = Listing.objects.create(
            title="Rejected Owner View",
            description="Visible to seller",
            price="5.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.REJECTED,
        )
        self.client.force_login(self.seller)
        response = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": rejected.listing_id}),
        )
        self.assertEqual(response.status_code, 200)

    def test_listing_detail_404_for_other_user_pending(self):
        self.client.force_login(self.other)
        response = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 404)

    def test_approved_listing_visible_to_anonymous(self):
        response = self.client.get(
            reverse("listing_detail", kwargs={"listing_id": self.approved_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 200)

    def test_owner_sees_pending_on_account_page(self):
        self.client.force_login(self.seller)
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 200)
        user_listing_ids = {listing.listing_id for listing in response.context["user_listings"]}
        self.assertIn(self.pending_listing.listing_id, user_listing_ids)
        self.assertIn(self.approved_listing.listing_id, user_listing_ids)

    def test_account_pending_queue_for_superuser(self):
        superuser = User.objects.create_user(
            username="root",
            email="root@sfsu.edu",
            sfsu_email="root@sfsu.edu",
            password="pass1234",
            role=self.student_role,
            password_hash="hashed",
            is_superuser=True,
        )
        self.client.force_login(superuser)
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_admin"])
        queue_ids = {listing.listing_id for listing in response.context["pending_listings"]}
        self.assertIn(self.pending_listing.listing_id, queue_ids)

    def test_approve_endpoint_rejects_get(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_approve_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 405)

    def test_reject_endpoint_rejects_get(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("admin_reject_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 405)

    def test_non_admin_cannot_approve(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("admin_approve_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 404)
        self.pending_listing.refresh_from_db()
        self.assertEqual(self.pending_listing.approval_status, ApprovalStatus.PENDING)

    def test_non_admin_cannot_reject(self):
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("admin_reject_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
            {"rejection_reason": "Should not work"},
        )
        self.assertEqual(response.status_code, 404)
        self.pending_listing.refresh_from_db()
        self.assertEqual(self.pending_listing.approval_status, ApprovalStatus.PENDING)
        self.assertEqual(self.pending_listing.rejection_reason, "")

    def test_approve_clears_rejection_reason(self):
        self.pending_listing.approval_status = ApprovalStatus.REJECTED
        self.pending_listing.rejection_reason = "Initial rejection"
        self.pending_listing.save(update_fields=["approval_status", "rejection_reason"])

        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("admin_approve_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.assertEqual(response.status_code, 302)
        self.pending_listing.refresh_from_db()
        self.assertEqual(self.pending_listing.approval_status, ApprovalStatus.APPROVED)
        self.assertEqual(self.pending_listing.rejection_reason, "")

    def test_account_pending_queue_excludes_approved_and_rejected(self):
        Listing.objects.create(
            title="Already Approved",
            description="Skipped",
            price="1.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.APPROVED,
        )
        Listing.objects.create(
            title="Already Rejected",
            description="Skipped",
            price="1.00",
            listing_type=ListingType.PRODUCT,
            intent=ListingIntent.FOR_SALE,
            condition="Good",
            category=self.category,
            seller=self.seller,
            approval_status=ApprovalStatus.REJECTED,
        )

        self.client.force_login(self.admin)
        response = self.client.get(reverse("account"))
        self.assertEqual(response.status_code, 200)
        queue_ids = {listing.listing_id for listing in response.context["pending_listings"]}
        self.assertEqual(queue_ids, {self.pending_listing.listing_id})

    def test_approved_after_approve_appears_in_category(self):
        self.client.force_login(self.admin)
        self.client.post(
            reverse("admin_approve_listing", kwargs={"listing_id": self.pending_listing.listing_id}),
        )
        self.client.logout()
        response = self.client.get(
            reverse("category_listings", kwargs={"category_id": self.category.category_id}),
        )
        listing_ids = {listing.listing_id for listing in response.context["listings"]}
        self.assertIn(self.pending_listing.listing_id, listing_ids)
