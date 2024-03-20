import csv
import logging
import os
import uuid
from datetime import datetime
from tempfile import SpooledTemporaryFile

from django.contrib.auth import get_user_model
from django.core.files import File
from django.core.files.storage import default_storage
from pathvalidate import sanitize_filename

from async_downloads.settings import (
    COLLECTION_KEY_FORMAT,
    IN_MEMORY_MAX_SIZE_BYTES,
    CSS_CLASS,
    PATH_PREFIX,
    TIMEOUT,
    WS_MODE,
    cache,
)
if WS_MODE:
    from async_downloads.ws_consumers import ws_init_download, ws_update_download

logger = logging.getLogger(__name__)


def get_username(user):
    username = None
    user_model = get_user_model()
    if isinstance(user, user_model):
        username = user.username
    elif isinstance(user, int):
        username = user_model.objects.get(pk=user).username
    else:
        return user
    return username


def get_collection_key(user):
    return COLLECTION_KEY_FORMAT.format(get_username(user))


def init_download(user, filename, name=None):
    download_key = f"{uuid.uuid4()}"
    filename = sanitize_filename(filename)
    filepath = os.path.join(PATH_PREFIX, download_key, filename)
    # TODO: consider inserting the collection key in here, so that it can be
    #  "touched" (`cache.touch`) to avoid the potential of the collection expiring
    #  before its downloads do
    download = {
        "user": get_username(user),
        "timestamp": datetime.now(),
        "filepath": filepath,
        "name": name or filename,
        "complete": False,
        "errors": "",
        "percentage": 0,
        "css_class": CSS_CLASS,
        "url": "",
    }
    collection_key = get_collection_key(user)
    # TODO: locking mechanism - consider https://pypi.org/project/django-cache-lock/
    # TODO: build the cleanup of expired keys into this?
    #  (since we are already modifying the cache entry)
    download_keys = [download_key] + cache.get(collection_key, [])
    cache.set(collection_key, download_keys, TIMEOUT)
    cache.set(download_key, download, TIMEOUT)
    if WS_MODE:
        ws_init_download(download_key)
    return collection_key, download_key


def save_download(download_key, iterable=None, file=None, encoding="utf-8"):
    # file is a BytesIO object
    download = cache.get(download_key)
    if not download:
        return
    if iterable is not None:
        try:
            with SpooledTemporaryFile(
                max_size=IN_MEMORY_MAX_SIZE_BYTES,
                mode="w+",
                newline="",
                encoding=encoding,
            ) as temp_file:
                writer = csv.writer(temp_file, lineterminator="\n")
                for row in iterable:
                    writer.writerow(row)
                # Force any remaining bytes in the buffer
                temp_file.flush()
                default_storage.save(download["filepath"], temp_file._file.buffer)
        except Exception as e:
            logger.exception(
                "Download failed with type: iterable key: %s name: %s error: %s",
                download_key,
                download.get("name"),
                str(e)
            )
            download["errors"] = str(e)
    elif file is not None:
        try:
            default_storage.save(download["filepath"], File(file))
        except Exception as e:
            logger.exception(
                "Download failed with type: File key: %s name: %s error: %s",
                download_key,
                download.get("name"),
                str(e)
            )
            download["errors"] = str(e)
    download["complete"] = True
    download["percentage"] = 100
    download["url"] = default_storage.url(download["filepath"])
    cache.set(download_key, download, TIMEOUT)
    if WS_MODE:
        ws_update_download(download_key)


def set_percentage(download_key, percentage):
    download = cache.get(download_key)
    if not download:
        return
    # Cap percentage between 0 and 100 and ensure it is an int
    download["percentage"] = min(max(0, int(percentage)), 100)
    cache.set(download_key, download, TIMEOUT)
    if WS_MODE:
        ws_update_download(download_key)


def update_percentage(download_key, total, cur, resolution=10):
    # Cap between 1 and 100, as there is no point in higher resolution,
    # and lower than 1 is invalid
    resolution = min(max(1, resolution), 100)
    for x in range(1, resolution):
        if cur + 1 == total // resolution * x:
            set_percentage(download_key, (100 / resolution) * x)
            break


def cleanup_collection(collection_key):
    # TODO: clean up files
    #  need to delete the file first, then the directory
    #    default_storage.delete(f for f in default_storage.listdir(os.path.join(PATH_PREFIX, download_key)))
    #    default_storage.delete(os.path.join(PATH_PREFIX, download_key))
    stored_keys = cache.get(collection_key, [])
    active_keys = [key for key in stored_keys if cache.get(key) is not None]
    # Avoid cache write if possible to reduce chance of clobbering
    if len(active_keys) != len(stored_keys):
        cache.set(collection_key, active_keys)
    # cache.set(
    #     collection_key, [key for key in cache.get(collection_key, []) if cache.get(key) is not None]
    # )


def set_error(download_key, error):
    download = cache.get(download_key)
    if not download:
        return

    logger.error(
        "Download failed with type: set_error key: %s name: %s error: %s",
        download_key,
        download.get("name"),
        str(error)
    )

    download["errors"] = str(error)
    download["complete"] = True
    download["percentage"] = 100
    cache.set(download_key, download, TIMEOUT)
    if WS_MODE:
        ws_update_download(download_key)
