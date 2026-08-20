"""
Broadcast newly-created Notification rows over WebSocket
to the recipient's personal channel.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import Notification


@receiver(post_save, sender=Notification)
def broadcast_new_notification(sender, instance, created, **kwargs):
    if not created:
        return

    channel_layer = get_channel_layer()
    if channel_layer is None:
        return

    async_to_sync(channel_layer.group_send)(
        f'user_{instance.recipient_id}',
        {
            'type': 'notification.new',
            'notification': {
                'id': instance.id,
                'message': instance.message,
                'ticket_id': instance.ticket_id,
                'is_read': instance.is_read,
                'created_at': instance.created_at.isoformat(),
            },
        }
    )