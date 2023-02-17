import json
import os

from asgiref.sync import async_to_sync
from channels.db import database_sync_to_async
from channels.exceptions import DenyConnection
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.template.loader import render_to_string

import async_downloads.settings as settings
from async_downloads.settings import DOWNLOAD_TEMPLATE, WS_CHANNEL_NAME, cache


def _timestamp_to_str(timestamp):
    return timestamp.astimezone().isoformat()


def ws_init_download(download_key):
    download = cache.get(download_key)
    download["download_key"] = download_key
    download["timestamp"] = _timestamp_to_str(download["timestamp"])
    download["html"] = render_to_string(DOWNLOAD_TEMPLATE, {"downloads": [download]})
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"{WS_CHANNEL_NAME}_{download['user']}",
        {
            "type": "init_download",
            "data": {
                "download": download,
                "download_key": download_key,
            },
        },
    )


def ws_update_download(download_key):
    download = cache.get(download_key)
    download["timestamp"] = _timestamp_to_str(download["timestamp"])
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"{WS_CHANNEL_NAME}_{download['user']}",
        {
            "type": "update_single_download",
            "data": {
                "download": download,
                "download_key": download_key,
            },
        },
    )


class DownloadsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope["user"]
        if not user.is_authenticated:
            raise DenyConnection
        self.username = user.username
        self.user = await database_sync_to_async(get_user_model().objects.get)(
            username=self.username
        )
        self.user_group_name = f"{WS_CHANNEL_NAME}_{self.username}"
        await self.channel_layer.group_add(self.user_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, "user_group_name"):
            await self.channel_layer.group_discard(
                self.user_group_name, self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        event = data["eventType"]
        if event == "clearDownload":
            await self.clear_download(data["data"]["filepath"])
        if event == "initAllDownloads":
            await self.init_all_downloads()

    async def init_all_downloads(self):
        from async_downloads.cache import get_collection_key

        download_keys = cache.get(get_collection_key(self.user), [])
        downloads = []
        #  by default they are listed from newest
        for download_key in reversed(download_keys):
            dl = cache.get(download_key)
            if not dl:
                continue
            dl["download_key"] = download_key
            dl["timestamp"] = _timestamp_to_str(dl["timestamp"])
            dl["html"] = render_to_string(DOWNLOAD_TEMPLATE, {"downloads": [dl]})
            downloads.append({"download": dl, "download_key": download_key})
        await self.send(
            json.dumps(
                {"eventType": settings.EVENT_TYPE_INIT_ALL_DOWNLOADS, "data": downloads}
            )
        )

    async def remove_single_download(self, data):
        await self.send(
            json.dumps({"eventType": settings.EVENT_TYPE_REMOVE_DOWNLOAD, **data})
        )

    async def update_single_download(self, data):
        await self.send(
            json.dumps({"eventType": settings.EVENT_TYPE_UPDATE_DOWNLOAD, **data})
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
            {"type": "remove_single_download", "data": {"download_key": download_key}},
        )
