from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Ticket, TicketCategory


class TicketRBACTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer1 = User.objects.create_user(
            phone_number='03001111111', password='pass123', role='CUSTOMER'
        )
        self.customer2 = User.objects.create_user(
            phone_number='03002222222', password='pass123', role='CUSTOMER'
        )
        self.category = TicketCategory.objects.create(name='Network')
        self.ticket = Ticket.objects.create(
            title='Test issue', description='desc', category=self.category,
            customer=self.customer1
        )

    def _login(self, user):
        response = self.client.post('/api/users/login/', {
            'reg_number': user.reg_number, 'password': 'pass123'
        })
        token = response.data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')

    def test_customer_sees_own_ticket(self):
        self._login(self.customer1)
        response = self.client.get(f'/api/tickets/{self.ticket.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customer_cannot_see_others_ticket(self):
        self._login(self.customer2)
        response = self.client.get(f'/api/tickets/{self.ticket.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_customer_ticket_auto_assigned_to_self(self):
        self._login(self.customer2)
        response = self.client.post('/api/tickets/', {
            'title': 'New issue', 'description': 'desc', 'category': self.category.id
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['customer'], self.customer2.id)

    def test_dashboard_blocked_for_customer(self):
        self._login(self.customer1)
        response = self.client.get('/api/dashboard/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)