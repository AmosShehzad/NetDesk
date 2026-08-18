from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from .models import Bill


class BillingTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            phone_number='03401111111', password='testpass123', role='CUSTOMER'
        )
        self.other = User.objects.create_user(
            phone_number='03402222222', password='testpass123', role='CUSTOMER'
        )
        self.bill = Bill.objects.create(
            customer=self.customer, amount=1500.00,
            due_date='2026-09-01', status='UNPAID',
        )

    def test_customer_sees_own_bills(self):
        self.client.force_authenticate(user=self.customer)
        res = self.client.get('/api/billing/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

    def test_customer_cannot_see_others_bills(self):
        self.client.force_authenticate(user=self.other)
        res = self.client.get('/api/billing/')
        self.assertEqual(len(res.data['results']), 0)