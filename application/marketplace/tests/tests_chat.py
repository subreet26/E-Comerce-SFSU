from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Listing, Message, Category
from . import context_processors

User = get_user_model()

class ChatFeatureTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()

        # Create users
        self.seller = User.objects.create_user(username='seller', email='seller@example.com', sfsu_email='seller@sfsu.edu', password='pass')
        self.buyer1 = User.objects.create_user(username='buyer1', email='buyer1@example.com', sfsu_email='buyer1@sfsu.edu', password='pass')
        self.buyer2 = User.objects.create_user(username='buyer2', email='buyer2@example.com', sfsu_email='buyer2@sfsu.edu', password='pass')

        # Ensure marketplace fields exist if necessary
        # create categories and listings
        self.category = Category.objects.create(category_name='Test Cat')
        self.listing1 = Listing.objects.create(title='Item 1', price='10.00', listing_type='product', intent='for_sale', category=self.category, seller=self.seller)
        self.listing2 = Listing.objects.create(title='Item 2', price='20.00', listing_type='product', intent='for_sale', category=self.category, seller=self.seller)

    def test_send_message_redirects_to_chat_and_creates_message(self):
        self.client.login(username='buyer1', password='pass')
        url = reverse('send_message', args=[self.listing1.listing_id])
        resp = self.client.post(url, {'content': 'Hello seller'})
        # Should redirect to chat thread URL
        expected = reverse('chat') + f"?listing={self.listing1.listing_id}&with={self.seller.id}"
        self.assertRedirects(resp, expected, fetch_redirect_response=False)

        # Message should exist
        msg = Message.objects.filter(sender=self.buyer1, receiver=self.seller, listing=self.listing1, content='Hello seller').first()
        self.assertIsNotNone(msg)

    def test_chat_poll_returns_new_messages_for_participant(self):
        # buyer1 sends a message to seller
        Message.objects.create(sender=self.buyer1, receiver=self.seller, listing=self.listing1, content='Hi seller')

        # seller polls for new messages after 0
        self.client.login(username='seller', password='pass')
        poll_url = reverse('chat_poll')
        resp = self.client.get(poll_url, {'listing': self.listing1.listing_id, 'with': self.buyer1.id, 'after_id': 0})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('messages', data)
        self.assertTrue(any(m['content'] == 'Hi seller' for m in data['messages']))

    def test_chat_threads_poll_returns_threads_with_unread_counts(self):
        # buyer1 sends on listing1, buyer2 sends on listing2
        Message.objects.create(sender=self.buyer1, receiver=self.seller, listing=self.listing1, content='Msg1')
        Message.objects.create(sender=self.buyer2, receiver=self.seller, listing=self.listing2, content='Msg2')

        self.client.login(username='seller', password='pass')
        poll_url = reverse('chat_threads_poll')
        resp = self.client.get(poll_url)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn('threads', data)
        # Should contain two threads
        listing_ids = {t['listing_id'] for t in data['threads']}
        self.assertTrue({self.listing1.listing_id, self.listing2.listing_id}.issubset(listing_ids))
        # Unread counts should be positive
        for t in data['threads']:
            if t['listing_id'] in (self.listing1.listing_id, self.listing2.listing_id):
                self.assertGreaterEqual(t['unread_count'], 1)

    def test_context_processor_includes_unread_count(self):
        # create one unread message for seller
        Message.objects.create(sender=self.buyer1, receiver=self.seller, listing=self.listing1, content='Hey')
        request = self.factory.get('/')
        request.user = self.seller
        ctx = context_processors.marketplace_globals(request)
        self.assertIn('unread_count', ctx)
        self.assertEqual(ctx['unread_count'], 1)
