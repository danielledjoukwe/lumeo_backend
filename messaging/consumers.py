import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import Thread, Message

User = get_user_model()


class ThreadConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for a single thread.
    Room group name: thread_{thread_id}

    On connect  — join the room group
    On receive  — save message to DB, broadcast to group
    On disconnect — leave the room group
    """

    async def connect(self):
        self.thread_id  = self.scope['url_route']['kwargs']['thread_id']
        self.room_group = f'thread_{self.thread_id}'
        self.user       = self.scope['user']

        # Reject unauthenticated connections
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        # Reject if not a participant
        is_participant = await self._is_participant()
        if not is_participant:
            await self.close()
            return

        # Join room group
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data):
        """
        Handle incoming WebSocket message from the client.
        Expected JSON: { "body": "..." }
        """
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON."}))
            return

        body = data.get('body', '').strip()
        if not body:
            await self.send(text_data=json.dumps({"error": "Le message ne peut pas être vide."}))
            return

        # Save to DB
        message = await self._create_message(body)

        # Broadcast to all clients in the room
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type':       'chat_message',   # → calls chat_message() below
                'id':         str(message.id),
                'body':       message.body,
                'sender_id':  str(self.user.id),
                'sender_name': self.user.full_name,
                'created_at': message.created_at.isoformat(),
                'message_type': message.message_type,
            }
        )

    async def chat_message(self, event):
        """
        Receive a broadcast from the group and forward it to the WebSocket client.
        """
        await self.send(text_data=json.dumps(event))

    # ── DB helpers (sync → async) ─────────────────────────────────────────────

    @database_sync_to_async
    def _is_participant(self):
        try:
            thread = Thread.objects.select_related(
                'application__campaign__business__user',
                'application__influencer__user',
            ).get(pk=self.thread_id)
            return thread.is_participant(self.user)
        except Thread.DoesNotExist:
            return False

    @database_sync_to_async
    def _create_message(self, body):
        thread  = Thread.objects.get(pk=self.thread_id)
        message = Message.objects.create(
            thread       = thread,
            sender       = self.user,
            message_type = Message.Type.USER,
            body         = body,
        )
        # Bump thread updated_at so inbox re-orders correctly
        thread.save(update_fields=['updated_at'])
        return message