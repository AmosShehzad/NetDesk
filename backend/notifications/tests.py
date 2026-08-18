from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from tickets.models import Ticket, TicketCategory
from .models import Notification, Announcement


class NotificationTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            phone_number='03301111111', password='testpass123', role='CUSTOMER'
        )
        self.manager = User.objects.create_user(
            phone_number='03302222222', password='testpass123', role='MANAGER'
        )

    def test_customer_sees_only_own_notifications(self):
        Notification.objects.create(recipient=self.customer, message='Test notif')
        Notification.objects.create(recipient=self.manager, message='Manager notif')

        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/notifications/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

    def test_mark_notification_read(self):
        notif = Notification.objects.create(recipient=self.customer, message='Unread')
        self.client.force_authenticate(user=self.customer)
        res = self.client.patch(f'/api/notifications/{notif.id}/', {'is_read': True})
        self.assertEqual(res.status_code, 200)
        notif.refresh_from_db()
        self.assertTrue(notif.is_read)

    def test_announcement_creates_notifications(self):
        Announcement.objects.create(
            title='Maintenance',
            message='Scheduled maintenance tonight.',
            created_by=self.manager,
        )
        customer_notifs = Notification.objects.filter(recipient=self.customer)
        self.assertEqual(customer_notifs.count(), 1)
        self.assertIn('Maintenance', customer_notifs.first().message)