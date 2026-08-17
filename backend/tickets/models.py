from django.db import models
from django.conf import settings
from django.utils import timezone

class TicketCategory(models.Model):
    """
    Simple lookup table for ticket categories (e.g. Network Outage, Billing).
    Kept as its own model instead of hardcoded choices, so Admins can add
    new categories later without touching code.
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Ticket Categories"


class Ticket(models.Model):
    """
    Core model of the whole project. Represents one customer support ticket
    and tracks its full lifecycle from creation to closure.
    """

    class Status(models.TextChoices):
        OPEN = 'OPEN', 'Open'
        ASSIGNED = 'ASSIGNED', 'Assigned'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        WAITING_CUSTOMER = 'WAITING_CUSTOMER', 'Waiting For Customer'
        RESOLVED = 'RESOLVED', 'Resolved'
        CLOSED = 'CLOSED', 'Closed'

    class Priority(models.TextChoices):
        LOW = 'LOW', 'Low'
        MEDIUM = 'MEDIUM', 'Medium'
        HIGH = 'HIGH', 'High'
        CRITICAL = 'CRITICAL', 'Critical'
    ai_reply_count = models.IntegerField(default=0)
    escalated = models.BooleanField(default=False)
    ticket_number = models.CharField(max_length=20, unique=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField()

    category = models.ForeignKey(
        TicketCategory, on_delete=models.SET_NULL, null=True, related_name='tickets'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.MEDIUM)

    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='tickets_created', limit_choices_to={'role': 'CUSTOMER'},
    )
    assigned_agent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets_assigned_as_agent', limit_choices_to={'role': 'SUPPORT_AGENT'},
    )
    assigned_technician = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='tickets_assigned_as_technician', limit_choices_to={'role': 'TECHNICIAN'},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.ticket_number} - {self.title}"

    class Meta:
        ordering = ['-created_at']  # newest tickets first by default

    def assign_agent(self, agent):
        """Assigns a support agent and moves ticket to ASSIGNED status."""
        self.assigned_agent = agent
        self.status = self.Status.ASSIGNED
        self.save()

    def start_progress(self):
        """Moves ticket from ASSIGNED to IN_PROGRESS. Rejects invalid jumps."""
        if self.status != self.Status.ASSIGNED:
            raise ValueError("Ticket must be ASSIGNED before moving to IN_PROGRESS.")
        self.status = self.Status.IN_PROGRESS
        self.save()

    def mark_resolved(self):
        """Moves ticket to RESOLVED. Only valid from IN_PROGRESS or WAITING_CUSTOMER."""
        if self.status not in [self.Status.IN_PROGRESS, self.Status.WAITING_CUSTOMER]:
            raise ValueError("Ticket must be IN_PROGRESS or WAITING_CUSTOMER to resolve.")
        self.status = self.Status.RESOLVED
        self.save()

    def close(self):
        """Closes a resolved ticket and stamps the closed_at time."""
        if self.status != self.Status.RESOLVED:
            raise ValueError("Only RESOLVED tickets can be closed.")
        self.status = self.Status.CLOSED
        self.closed_at = timezone.now()
        self.save()


class TicketComment(models.Model):
    """
    Public conversation between customer and staff on a ticket.
    Visible to the ticket's customer AND all staff.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ticket_comments')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author.username or self.author.phone_number} on {self.ticket.ticket_number}"


class InternalNote(models.Model):
    """
    Staff-only note. Completely separate table from TicketComment —
    a Customer's queryset can never touch this model at all.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='internal_notes')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='internal_notes')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Internal note by {self.author.username or self.author.phone_number} on {self.ticket.ticket_number}"


class Attachment(models.Model):
    """
    File uploaded to a ticket. Never linked via a public URL —
    always accessed through the secured download endpoint.
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE, related_name='attachments')
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='ticket_attachments/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.ticket.ticket_number}"