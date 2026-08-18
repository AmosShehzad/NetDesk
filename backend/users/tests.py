from django.test import TestCase
from rest_framework.test import APIClient
from .models import User


class UserModelTests(TestCase):
    """Test user creation and registration numbers."""

    def test_customer_gets_cust_reg_number(self):
        user = User.objects.create_user(
            phone_number='03101111111', password='testpass123', role='CUSTOMER'
        )
        self.assertTrue(user.reg_number.startswith('CUST-'))

    def test_staff_gets_staff_reg_number(self):
        user = User.objects.create_user(
            phone_number='03102222222', password='testpass123', role='SUPPORT_AGENT'
        )
        self.assertTrue(user.reg_number.startswith('STAFF-'))

    def test_new_user_must_change_password(self):
        user = User.objects.create_user(
            phone_number='03103333333', password='testpass123', role='CUSTOMER'
        )
        self.assertTrue(user.must_change_password)

    def test_phone_number_unique(self):
        User.objects.create_user(
            phone_number='03104444444', password='testpass123', role='CUSTOMER'
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                phone_number='03104444444', password='testpass123', role='CUSTOMER'
            )


class AuthTests(TestCase):
    """Test login and password change flow."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone_number='03201111111', password='testpass123', role='CUSTOMER'
        )

    def test_login_with_reg_number(self):
        res = self.client.post('/api/users/login/', {
            'reg_number': self.user.reg_number,
            'password': 'testpass123',
        })
        self.assertEqual(res.status_code, 200)
        self.assertIn('access', res.data)
        self.assertIn('refresh', res.data)

    def test_login_wrong_password(self):
        res = self.client.post('/api/users/login/', {
            'reg_number': self.user.reg_number,
            'password': 'wrongpassword',
        })
        self.assertIn(res.status_code, [400, 401])

    def test_change_password(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.post('/api/users/change-password/', {
            'old_password': 'testpass123',
            'new_password': 'newsecurepass456',
        })
        self.assertEqual(res.status_code, 200)
        self.user.refresh_from_db()
        self.assertFalse(self.user.must_change_password)
        self.assertTrue(self.user.check_password('newsecurepass456'))

    def test_protected_route_without_token(self):
        res = self.client.get('/api/users/me/')
        self.assertEqual(res.status_code, 401)

    def test_me_endpoint(self):
        self.client.force_authenticate(user=self.user)
        res = self.client.get('/api/users/me/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data['phone_number'], '03201111111')