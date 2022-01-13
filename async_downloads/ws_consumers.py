import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer

import async_downloads.settings as settings
from async_downloads.settings import WS_CHANNEL_NAME


def ws_update_downloads(username):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"{WS_CHANNEL_NAME}_{username}",
        {"type": "update_downloads_dropdown"},
    )


class DownloadsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        username = self.scope["url_route"]["kwargs"]["username"]
        self.user_group_name = f"{WS_CHANNEL_NAME}_{username}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        pass

    async def update_downloads_dropdown(self, event):
        await self.send(
            json.dumps({"eventType": settings.EVENT_TYPE_REFRESH_DOWNLOADS})
        )
