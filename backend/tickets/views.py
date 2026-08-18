import logging

import httpx
from django.conf import settings
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.http import FileResponse, Http404
from django.utils import timezone
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsManagerOrAdmin, IsStaffRole
from .models import Ticket, TicketCategory, TicketComment, InternalNote, Attachment
from .serializers import (
    TicketSerializer, TicketCategorySerializer,
    TicketCommentSerializer, InternalNoteSerializer, AttachmentSerializer,
)

logger = logging.getLogger(__name__)

AI_SERVICE_URL = settings.AI_SERVICE_URL
MAX_AI_REPLIES = 3

TROUBLESHOOTING_TIPS = {
    'NetworkOutage': "Please try restarting your router (unplug for 30 seconds, then plug back in) and check if neighbors are also affected.",
    'SlowSpeed': "Try disconnecting other devices and running a speed test after restarting your router.",
    'Billing': "You can check your latest bill and payment status under 'My Account' in the portal.",
    'Installation': "Our installation team typically responds within 24-48 hours. Please ensure someone is available at the address on file.",
    'Other': "Thank you for reaching out — our support team will review your request shortly.",
}


def get_ai_assistant_user():
    """System account for AI replies. Created once, reused after."""
    from users.models import User
    user, created = User.objects.get_or_create(
        phone_number='00000000000',
        defaults={'role': 'SUPPORT_AGENT', 'username': 'AI Assistant'}
    )
    if created:
        user.set_unusable_password()
        user.save()
    return user


def notify_staff_of_escalation(ticket):
    """Notifies every Manager/Admin that a ticket needs human help."""
    from users.models import User
    from notifications.models import Notification

    staff = User.objects.filter(role__in=['MANAGER', 'ADMIN'])
    Notification.objects.bulk_create([
        Notification(
            recipient=s, ticket=ticket,
            message=f"{ticket.customer.reg_number} needs help on {ticket.ticket_number} — AI could not resolve it."
        )
        for s in staff
    ])
    logger.info(f"Ticket {ticket.ticket_number} escalated to {staff.count()} staff members")


class TicketCategoryViewSet(viewsets.ModelViewSet):
    """Simple CRUD for categories — only staff should manage these in practice,
    but we're keeping permissions simple for MVP (any authenticated user can read;
    tightening write access is a fast follow, flagged here not silently skipped)."""
    queryset = TicketCategory.objects.all()
    serializer_class = TicketCategorySerializer
    permission_classes = [permissions.IsAuthenticated]


class TicketViewSet(viewsets.ModelViewSet):
    """
    Core Ticket API. get_queryset() is where RBAC actually happens:
    each role sees a different slice of the Ticket table.
    """
    serializer_class = TicketSerializer
    permission_classes = [permissions.IsAuthenticated]

    filterset_fields = ['status', 'priority', 'category']
    search_fields = ['ticket_number', 'title', 'description']
    ordering_fields = ['created_at', 'updated_at', 'priority']

    def get_queryset(self):
        user = self.request.user
        # select_related pre-fetches related tables in ONE query instead of many —
        # this is the "Query Optimization" concept from the concept list.
        base = Ticket.objects.select_related('customer', 'assigned_agent', 'category')

        if user.role == 'CUSTOMER':
            return base.filter(customer=user)
        elif user.role == 'SUPPORT_AGENT':
            return base.filter(assigned_agent=user)
        elif user.role == 'TECHNICIAN':
            return base.filter(assigned_technician=user)
        elif user.role in ['MANAGER', 'ADMIN']:
            return base.all()
        return base.none()  # unknown role sees nothing, safe default

    def perform_create(self, serializer):
        ticket = serializer.save(customer=self.request.user)
        ai_data = None

        try:
            response = httpx.post(
                f"{AI_SERVICE_URL}/ai/analyze",
                json={"text": ticket.description, "customer_id": str(ticket.customer.id)},
                timeout=30.0
            )
            if response.status_code == 200:
                ai_data = response.json()
        except Exception as e:
            logger.error(f"AI service unreachable on ticket creation: {e}")
            ai_data = None

        ai_user = get_ai_assistant_user()

        if ai_data and 'priority' in ai_data:
            ticket.priority = ai_data['priority']
            ticket.ai_reply_count = 1
            ticket.save()

            # If the AI decided to escalate, respect that decision
            if ai_data.get('should_escalate', False):
                ticket.escalated = True
                ticket.save()
                TicketComment.objects.create(
                    ticket=ticket, author=ai_user,
                    message=ai_data.get('suggested_reply', 'Our support team will assist you shortly.')
                )
                notify_staff_of_escalation(ticket)
                logger.info(f"Ticket {ticket.ticket_number} auto-escalated by AI (reason: {ai_data.get('escalation_reason', 'N/A')})")
            else:
                # AI is confident — post its reply
                category = ai_data.get('category', 'Other')
                tip = TROUBLESHOOTING_TIPS.get(category, TROUBLESHOOTING_TIPS['Other'])
                reply_text = f"{ai_data.get('suggested_reply', '')}\n\nQuick tip: {tip}"
                TicketComment.objects.create(ticket=ticket, author=ai_user, message=reply_text)

                # Still flag urgent tickets for staff awareness
                if ai_data['priority'] in ['HIGH', 'CRITICAL']:
                    TicketComment.objects.create(
                        ticket=ticket, author=ai_user,
                        message="This issue has been flagged as urgent. Our support team has been notified."
                    )
                    notify_staff_of_escalation(ticket)
        else:
            # AI unreachable — safe fallback
            TicketComment.objects.create(
                ticket=ticket, author=ai_user,
                message="Thank you for reporting this. Our support team will review your ticket and get back to you shortly."
            )


class TicketCommentViewSet(viewsets.ModelViewSet):
    """
    Public comments. Customer sees only comments on their own tickets.
    Staff sees comments on any ticket.
    """
    serializer_class = TicketCommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        ticket_id = self.request.query_params.get('ticket')
        base = TicketComment.objects.select_related('author', 'ticket')
        if ticket_id:
            base = base.filter(ticket_id=ticket_id)

        if user.role == 'CUSTOMER':
            return base.filter(ticket__customer=user)
        elif user.role in ['SUPPORT_AGENT', 'TECHNICIAN', 'MANAGER', 'ADMIN']:
            return base.all()
        return base.none()

    def perform_create(self, serializer):
        comment = serializer.save(author=self.request.user)
        ticket = comment.ticket

        # Only run AI flow if author is the customer, ticket isn't escalated, and limit isn't reached
        if self.request.user.role == 'CUSTOMER' and not ticket.escalated and ticket.ai_reply_count < MAX_AI_REPLIES:
            comments = ticket.comments.select_related('author').order_by('created_at')
            history = "\n".join([f"{c.author.username}: {c.message}" for c in comments])

            try:
                response = httpx.post(
                    f"{AI_SERVICE_URL}/ai/analyze",
                    json={
                        "text": f"Ticket conversation so far:\n{history}\n\nRespond helpfully to the customer's latest message.",
                        "customer_id": str(ticket.customer.id),
                    },
                    timeout=30.0
                )
                if response.status_code == 200:
                    ai_data = response.json()
                    ai_user = get_ai_assistant_user()

                    if ai_data.get('should_escalate', False):
                        ticket.escalated = True
                        ticket.save()
                        TicketComment.objects.create(
                            ticket=ticket, author=ai_user,
                            message=ai_data.get('suggested_reply', 'Our support team will assist you shortly.')
                        )
                        notify_staff_of_escalation(ticket)
                    else:
                        TicketComment.objects.create(
                            ticket=ticket, author=ai_user,
                            message=ai_data.get('suggested_reply', '')
                        )
                        ticket.ai_reply_count += 1
                        ticket.save()
            except Exception as e:
                logger.error(f"AI service error during comment follow-up: {e}")


class InternalNoteViewSet(viewsets.ModelViewSet):
    """
    Staff-only. IsStaffRole blocks Customers at the permission layer —
    a Customer gets 403 on this entire endpoint, no queryset trickery needed.
    """
    serializer_class = InternalNoteSerializer
    permission_classes = [permissions.IsAuthenticated, IsStaffRole]

    def get_queryset(self):
        ticket_id = self.request.query_params.get('ticket')
        base = InternalNote.objects.select_related('author', 'ticket')
        if ticket_id:
            base = base.filter(ticket_id=ticket_id)
        return base.all()

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class AttachmentViewSet(viewsets.ModelViewSet):
    """
    File upload + secured download. get_object() below reuses get_queryset(),
    so the download action is automatically permission-checked too.
    """
    serializer_class = AttachmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        user = self.request.user
        ticket_id = self.request.query_params.get('ticket')
        base = Attachment.objects.select_related('uploaded_by', 'ticket')
        if ticket_id:
            base = base.filter(ticket_id=ticket_id)

        if user.role == 'CUSTOMER':
            return base.filter(ticket__customer=user)
        elif user.role in ['SUPPORT_AGENT', 'TECHNICIAN', 'MANAGER', 'ADMIN']:
            return base.all()
        return base.none()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        # get_object() runs get_queryset() first — a Customer requesting
        # someone else's attachment gets 404 here, same as tickets.
        attachment = self.get_object()
        try:
            return FileResponse(
                attachment.file.open('rb'),
                as_attachment=True,
                filename=attachment.file.name.split('/')[-1],
            )
        except FileNotFoundError:
            raise Http404("File not found.")


class DashboardView(APIView):
    """
    Manager/Admin only. Returns aggregated ticket stats in one call.
    """
    permission_classes = [permissions.IsAuthenticated, IsManagerOrAdmin]

    def get(self, request):
        tickets = Ticket.objects.all()
        today = timezone.now().date()
        today_tickets = tickets.filter(created_at__date=today)

        # Status breakdown
        status_counts = dict(
            tickets.values_list('status').annotate(count=Count('id')).values_list('status', 'count')
        )

        # Priority breakdown
        priority_counts = dict(
            tickets.values_list('priority').annotate(count=Count('id')).values_list('priority', 'count')
        )

        # Category breakdown
        category_counts = list(
            tickets.values('category__name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )

        # Average resolution time (only for closed tickets)
        closed = tickets.filter(status='CLOSED', closed_at__isnull=False)
        avg_resolution = closed.annotate(
            resolution_time=ExpressionWrapper(
                F('closed_at') - F('created_at'), output_field=DurationField()
            )
        ).aggregate(avg=Avg('resolution_time'))
        avg_hours = None
        if avg_resolution['avg']:
            avg_hours = round(avg_resolution['avg'].total_seconds() / 3600, 1)

        # AI performance
        total_tickets = tickets.count() or 1
        ai_resolved = tickets.filter(escalated=False, status__in=['RESOLVED', 'CLOSED']).count()
        escalated_count = tickets.filter(escalated=True).count()

        # Daily report
        daily_report = {
            'date': str(today),
            'total_today': today_tickets.count(),
            'most_common_category': list(
                today_tickets.values('category__name')
                .annotate(count=Count('id'))
                .order_by('-count')[:1]
            ),
            'urgent_today': list(
                today_tickets.filter(priority__in=['HIGH', 'CRITICAL'])
                .values('ticket_number', 'title', 'priority')
            ),
        }

        return Response({
            'total_tickets': total_tickets,
            'status_counts': status_counts,
            'priority_counts': priority_counts,
            'category_counts': category_counts,
            'avg_resolution_hours': avg_hours,
            'ai_resolution_rate': round((ai_resolved / total_tickets) * 100, 1),
            'escalated_count': escalated_count,
            'open_tickets': status_counts.get('OPEN', 0),
            'daily_report': daily_report,
        })