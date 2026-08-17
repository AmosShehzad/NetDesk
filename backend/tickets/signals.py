from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Ticket


@receiver(pre_save, sender=Ticket)
def generate_ticket_number(sender, instance, **kwargs):
    """
    Runs automatically right before a Ticket is saved.
    If it's a new ticket (no ticket_number yet), generate one like TKT-2026-00001.
    """
    if not instance.ticket_number:
        year = timezone.now().year
        count = Ticket.objects.filter(created_at__year=year).count() + 1
        instance.ticket_number = f"TKT-{year}-{count:05d}"