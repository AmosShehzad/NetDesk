"""
Signal handlers that push events to WebSocket rooms.
Fires on comment create so every connected client (staff & customer)
gets the message instantly instead of waiting to poll.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import TicketComment
from .serializers import TicketCommentSerializer


@receiver(post_save, sender=TicketComment)
def broadcast_new_comment(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    payload = TicketCommentSerializer(instance).data

    # 1. Broadcast to everyone watching this ticket
    async_to_sync(channel_layer.group_send)(
        f'ticket_{instance.ticket_id}',
        {
            'type': 'comment.new',   # matches TicketConsumer.comment_new
            'comment': payload,
        }
    )

    # 2. Also nudge the ticket's customer via their notification channel
    # (so the notification bell can flash without a comment being on their currently-open page)
    customer_id = instance.ticket.customer_id
    if customer_id and instance.author_id != customer_id:
        async_to_sync(channel_layer.group_send)(
            f'user_{customer_id}',
            {
                'type': 'notification.new',
                'notification': {
                    'kind': 'new_comment',
                    'ticket_id': instance.ticket_id,
                    'ticket_number': instance.ticket.ticket_number,
                    'message': (instance.message or '')[:120],
                },
            }
        )