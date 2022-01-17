import json
import os

import requests
from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.core.cache import caches
from django.core.files.storage import default_storage

import async_downloads.settings as settings
from async_downloads.settings import WS_MODE, WS_CHANNEL_NAME

if WS_MODE:
    cache = caches["downloads"]


def ws_init_download(username, download_key):
    download = cache.get(download_key)
    download["timestamp"] = str(download["timestamp"])
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"{WS_CHANNEL_NAME}_{username}",
        {
            "type": "init_download",
            "data": {
                "download": download,
                "downloadKey": download_key,
            },
        },
    )


class DownloadsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.username = self.scope["user"].username
        self.user_group_name = f"{WS_CHANNEL_NAME}_{self.username}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data["eventType"]
        if event == "clearDownload":
            await self.clear_download(data["data"]["filepath"])
        if event == "getDownload":
            await self.update_single_download(data["downloadKey"])

    async def refresh_download_dropdown(self, data):
        await self.send(
            json.dumps({"eventType": settings.EVENT_TYPE_REFRESH_DOWNLOADS})
        )

    async def remove_single_download(self, data):
        await self.send(
            json.dumps({"eventType": settings.EVENT_TYPE_REMOVE_DOWNLOAD, **data})
        )

    async def update_single_download(self, download_key):
        download = cache.get(download_key)
        download["timestamp"] = str(download["timestamp"])
        await self.send(
            json.dumps(
                {
                    "eventType": settings.EVENT_TYPE_UPDATE_DOWNLOAD,
                    "data": {
                        "download": download,
                        "downloadKey": download_key,
                    },
                }
            )
        )

    async def init_download(self, data):
        await self.send(
            json.dumps({"eventType": settings.EVENT_TYPE_INIT_DOWNLOAD, **data})
        )

    async def clear_download(self, filepath):
        directory = os.path.split(filepath)[0]
        download_key = os.path.split(directory)[1]
        cache.delete(download_key)
        default_storage.delete(filepath)
        default_storage.delete(directory)
        await self.channel_layer.group_send(
            self.user_group_name,
            {"type": "remove_single_download", "data": {"downloadKey": download_key}},
        )
