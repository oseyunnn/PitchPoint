from django.test import SimpleTestCase
from django.urls import reverse


class GuestInboxTests(SimpleTestCase):
    def test_guest_can_open_empty_inbox(self):
        response = self.client.get(reverse("inbox:inbox"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You’re all caught up")