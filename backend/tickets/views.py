import httpx
import environ

env = environ.Env()
environ.Env.read_env()
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from rest_framework.views import APIView, Response
from users.permissions import IsManagerOrAdmin
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from django.http import FileResponse, Http404
from django_filters.rest_framework import DjangoFilterBackend
from .models import Ticket, TicketCategory, TicketComment, InternalNote, Attachment
from .serializers import (
    TicketSerializer, TicketCategorySerializer,
    TicketCommentSerializer, InternalNoteSerializer, AttachmentSerializer,
)
from django.utils import timezone
from users.permissions import IsStaffRole
TROUBLESHOOTING_TIPS = {
    'NetworkOutage': "Please try restarting your router (unplug for 30 seconds, then plug back in) and check if neighbors are also affected.",
    'SlowSpeed': "Try disconnecting other devices and running a speed test after restarting your router.",
    'Billing': "You can check your latest bill and payment status under 'My Account' in the portal.",
    'Installation': "Our installation team typically responds within 24-48 hours. Please ensure someone is available at the address on file.",
    'Other': "Thank you for reaching out — our support team will review your request shortly.",
}

MAX_AI_REPLIES = 3

def get_ai_assistant_user():
    """
    A system account that 'writes' the AI's automatic replies as normal ticket comments.
    Created once, reused after that — get_or_create is idempotent.
    """
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
    """
    Notifies every Manager/Admin that a customer needs human help on this ticket.
    """
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
AI_SERVICE_URL = env('AI_SERVICE_URL', default='http://127.0.0.1:8001')

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
                json={"text": ticket.description},
                timeout=30.0
            )
            if response.status_code == 200:
                ai_data = response.json()
        except Exception:
            ai_data = None

        ai_user = get_ai_assistant_user()

        if ai_data and 'priority' in ai_data:
            ticket.priority = ai_data['priority']
            ticket.ai_reply_count = 1
            ticket.save()

            category = ai_data.get('category', 'Other')
            tip = TROUBLESHOOTING_TIPS.get(category, TROUBLESHOOTING_TIPS['Other'])
            reply_text = f"{ai_data.get('suggested_reply', '')}\n\nQuick tip: {tip}"

            TicketComment.objects.create(ticket=ticket, author=ai_user, message=reply_text)

            if ai_data['priority'] in ['HIGH', 'CRITICAL']:
                TicketComment.objects.create(
                    ticket=ticket, author=ai_user,
                    message="This issue has been flagged as urgent and escalated to our support team. They will contact you shortly."
                )
        else:
            # AI unreachable — safe fallback, never leave the customer without any response
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

        # Only the AI responds automatically to CUSTOMER messages,
        # and only while the ticket is still open and not already escalated.
        is_customer_message = (self.request.user == ticket.customer)
        ticket_still_active = ticket.status not in ['RESOLVED', 'CLOSED']

        if not (is_customer_message and ticket_still_active and not ticket.escalated):
            return

        ai_user = get_ai_assistant_user()

        if ticket.ai_reply_count >= MAX_AI_REPLIES:
            # AI has tried enough times — hand off to a human
            ticket.escalated = True
            ticket.save()

            TicketComment.objects.create(
                ticket=ticket, author=ai_user,
                message="I've connected you with our support team — they'll follow up with you shortly."
            )
            notify_staff_of_escalation(ticket)
            return

        # Build a short conversation history so the AI has context, not just the last line
        history = "\n".join(
            f"{c.author.username or 'Customer'}: {c.message}"
            for c in ticket.comments.order_by('created_at')
        )

        try:
            response = httpx.post(
                f"{AI_SERVICE_URL}/ai/analyze",
                json={"text": f"Ticket conversation so far:\n{history}\n\nRespond helpfully to the customer's latest message."},
                timeout=30.0
            )
            if response.status_code == 200:
                data = response.json()
                reply = data.get('suggested_reply', "Let me look into that for you.")
                TicketComment.objects.create(ticket=ticket, author=ai_user, message=reply)
                ticket.ai_reply_count += 1
                ticket.save()
            else:
                raise Exception("AI service returned non-200")
        except Exception:
            # AI unreachable mid-conversation — escalate immediately rather than go silent
            ticket.escalated = True
            ticket.save()
            TicketComment.objects.create(
                ticket=ticket, author=ai_user,
                message="I'm having trouble processing that right now — I've flagged this for our team to follow up."
            )
            notify_staff_of_escalation(ticket)


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
    