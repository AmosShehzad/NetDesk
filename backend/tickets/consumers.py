"""
WebSocket consumers.
- TicketConsumer: per-ticket room, broadcasts new comments
- NotificationConsumer: per-user room, pushes notifications
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer


class TicketConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.ticket_id = self.scope['url_route']['kwargs']['ticket_id']
        self.group_name = f'ticket_{self.ticket_id}'
        user = self.scope.get('user')

        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected', 'ticket_id': self.ticket_id})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # Broadcast handler — called when someone posts a comment
    async def comment_new(self, event):
        await self.send_json({'type': 'comment.new', 'comment': event['comment']})


class NotificationConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated:
            await self.close(code=4001)
            return

        self.group_name = f'user_{user.id}'
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        await self.send_json({'type': 'connected'})

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def notification_new(self, event):
        await self.send_json({'type': 'notification.new', 'notification': event['notification']})