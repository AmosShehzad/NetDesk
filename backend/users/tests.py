from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


class AuthTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            phone_number='03001234567', password='testpass123', role='CUSTOMER'
        )
        self.manager = User.objects.create_user(
            phone_number='03007654321', password='testpass123', role='MANAGER'
        )

    def test_login_success(self):
        response = self.client.post('/api/users/login/', {
            'reg_number': self.customer.reg_number, 'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_wrong_password_fails(self):
        response = self.client.post('/api/users/login/', {
            'reg_number': self.customer.reg_number, 'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_reg_number_auto_generated(self):
        self.assertTrue(self.customer.reg_number.startswith('CUST-'))
        self.assertTrue(self.manager.reg_number.startswith('STAFF-'))

    def test_profile_requires_auth(self):
        response = self.client.get('/api/users/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)