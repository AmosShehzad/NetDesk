from django.db.models.signals import post_save
from django.dispatch import receiver
from tickets.models import Ticket, TicketComment
from .models import Notification


@receiver(post_save, sender=Ticket)
def notify_on_ticket_change(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.customer,
            ticket=instance,
            message=f"Your ticket {instance.ticket_number} was created."
        )
    else:
        Notification.objects.create(
            recipient=instance.customer,
            ticket=instance,
            message=f"Ticket {instance.ticket_number} status updated to {instance.get_status_display()}."
        )
        if instance.assigned_agent:
            Notification.objects.create(
                recipient=instance.assigned_agent,
                ticket=instance,
                message=f"You were assigned ticket {instance.ticket_number}."
            )


@receiver(post_save, sender=TicketComment)
def notify_on_new_comment(sender, instance, created, **kwargs):
    if not created:
        return
    ticket = instance.ticket
    if instance.author == ticket.customer and ticket.assigned_agent:
        Notification.objects.create(
            recipient=ticket.assigned_agent,
            ticket=ticket,
            message=f"Customer replied on ticket {ticket.ticket_number}."
        )
    elif instance.author != ticket.customer:
        Notification.objects.create(
            recipient=ticket.customer,
            ticket=ticket,
            message=f"Support replied on ticket {ticket.ticket_number}."
        )
from .models import Announcement


@receiver(post_save, sender=Announcement)
def broadcast_announcement(sender, instance, created, **kwargs):
    if not created:
        return
    from users.models import User
    customers = User.objects.filter(role='CUSTOMER')
    Notification.objects.bulk_create([
        Notification(recipient=c, ticket=None, message=instance.message)
        for c in customers
    ])