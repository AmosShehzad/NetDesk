from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from users.models import User
from .models import Ticket, TicketCategory


class TicketLifecycleTests(TestCase):
    """Test the full ticket state machine."""

    def setUp(self):
        self.category = TicketCategory.objects.create(name='NetworkOutage')
        self.customer = User.objects.create_user(
            phone_number='03001111111', password='testpass123', role='CUSTOMER'
        )
        self.agent = User.objects.create_user(
            phone_number='03002222222', password='testpass123', role='SUPPORT_AGENT'
        )
        self.manager = User.objects.create_user(
            phone_number='03003333333', password='testpass123', role='MANAGER'
        )
        self.ticket = Ticket.objects.create(
            customer=self.customer,
            category=self.category,
            title='No internet',
            description='My internet has been down since morning.',
        )

    def test_ticket_created_with_open_status(self):
        self.assertEqual(self.ticket.status, 'OPEN')

    def test_assign_agent_changes_status(self):
        self.ticket.assign_agent(self.agent)
        self.assertEqual(self.ticket.status, 'ASSIGNED')
        self.assertEqual(self.ticket.assigned_agent, self.agent)

    def test_start_progress_requires_assigned(self):
        with self.assertRaises(ValueError):
            self.ticket.start_progress()

    def test_start_progress_from_assigned(self):
        self.ticket.assign_agent(self.agent)
        self.ticket.start_progress()
        self.assertEqual(self.ticket.status, 'IN_PROGRESS')

    def test_resolve_requires_in_progress(self):
        with self.assertRaises(ValueError):
            self.ticket.mark_resolved()

    def test_close_requires_resolved(self):
        with self.assertRaises(ValueError):
            self.ticket.close()

    def test_full_lifecycle(self):
        self.ticket.assign_agent(self.agent)
        self.ticket.start_progress()
        self.ticket.mark_resolved()
        self.ticket.close()
        self.assertEqual(self.ticket.status, 'CLOSED')
        self.assertIsNotNone(self.ticket.closed_at)

    def test_ticket_number_generated(self):
        self.assertTrue(self.ticket.ticket_number.startswith('TKT-'))


class TicketPermissionTests(TestCase):
    """Test that RBAC actually works."""

    def setUp(self):
        self.client = APIClient()
        self.category = TicketCategory.objects.create(name='SlowSpeed')

        self.customer1 = User.objects.create_user(
            phone_number='03011111111', password='testpass123', role='CUSTOMER'
        )
        self.customer2 = User.objects.create_user(
            phone_number='03012222222', password='testpass123', role='CUSTOMER'
        )
        self.agent = User.objects.create_user(
            phone_number='03013333333', password='testpass123', role='SUPPORT_AGENT'
        )
        self.manager = User.objects.create_user(
            phone_number='03014444444', password='testpass123', role='MANAGER'
        )

        self.ticket1 = Ticket.objects.create(
            customer=self.customer1, category=self.category,
            title='Slow speed', description='Very slow.'
        )

    def test_customer_sees_only_own_tickets(self):
        self.client.force_authenticate(user=self.customer1)
        res = self.client.get('/api/tickets/')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data['results']), 1)

    def test_customer_cannot_see_other_tickets(self):
        self.client.force_authenticate(user=self.customer2)
        res = self.client.get('/api/tickets/')
        self.assertEqual(len(res.data['results']), 0)

    def test_manager_sees_all_tickets(self):
        self.client.force_authenticate(user=self.manager)
        res = self.client.get('/api/tickets/')
        self.assertEqual(len(res.data['results']), 1)

    def test_unauthenticated_blocked(self):
        res = self.client.get('/api/tickets/')
        self.assertEqual(res.status_code, 401)

    def test_customer_can_create_ticket(self):
        self.client.force_authenticate(user=self.customer1)
        res = self.client.post('/api/tickets/', {
            'category': self.category.id,
            'title': 'New issue',
            'description': 'Something broke',
        })
        self.assertIn(res.status_code, [200, 201])

    def test_dashboard_blocked_for_customer(self):
        self.client.force_authenticate(user=self.customer1)
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 403)

    def test_dashboard_works_for_manager(self):
        self.client.force_authenticate(user=self.manager)
        res = self.client.get('/api/dashboard/')
        self.assertEqual(res.status_code, 200)
        self.assertIn('total_tickets', res.data)
        self.assertIn('status_counts', res.data)
        self.assertIn('ai_resolution_rate', res.data)

    def test_internal_notes_blocked_for_customer(self):
        self.client.force_authenticate(user=self.customer1)
        res = self.client.get('/api/tickets/internal-notes/')
        self.assertEqual(res.status_code, 403)