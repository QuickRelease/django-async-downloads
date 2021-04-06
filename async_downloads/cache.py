import csv
from datetime import datetime
from io import StringIO
import logging
import os
import uuid

from django.core.cache import cache
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from pathvalidate import sanitize_filename

from async_downloads.settings import COLLECTION_KEY_FORMAT, PATH_PREFIX, TIMEOUT

logger = logging.getLogger(__name__)


def get_collection_key(pk):
    return COLLECTION_KEY_FORMAT.format(pk)


def init_download(pk, filename, name=None):
    download_key = f"{uuid.uuid4()}"
    filename = sanitize_filename(filename)
    filepath = os.path.join(PATH_PREFIX, download_key, filename)
    # TODO: consider inserting the collection key in here, so that it can be
    #  "touched" (`cache.touch`) to avoid the potential of the collection expiring
    #  before its downloads do
    download = {
        "timestamp": datetime.now(),
        "filepath": filepath,
        "name": name or filename,
        "complete": False,
        "errors": "",
        "percentage": 0,
    }
    collection_key = get_collection_key(pk)
    # TODO: locking mechanism - consider https://pypi.org/project/django-cache-lock/
    # TODO: build the cleanup of expired keys into this?
    #  (since we are already modifying the cache entry)
    download_keys = [download_key] + cache.get(collection_key, [])
    cache.set(collection_key, download_keys, TIMEOUT)
    cache.set(download_key, download, TIMEOUT)
    return collection_key, download_key


def save_download(download_key, iterable=None, file=None):
    # file is a BytesIO object
    download = cache.get(download_key)
    if not download:
        return
    if iterable is not None:
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\n")
        try:
            for row in iterable:
                writer.writerow(row)
            default_storage.save(download["filepath"], ContentFile(output.getvalue().encode()))
        except Exception as e:
            logger.exception(
                "Download failed with type: iterable key: %s name: %s",
                download_key,
                download.get("name"),
            )
            download["errors"] = str(e)
    elif file is not None:
        try:
            default_storage.save(download["filepath"], File(file))
        except Exception as e:
            logger.exception(
                "Download failed with type: File key: %s name: %s",
                download_key,
                download.get("name"),
            )
            download["errors"] = str(e)
    download["complete"] = True
    download["percentage"] = 100
    cache.set(download_key, download, TIMEOUT)


def set_percentage(download_key, percentage):
    download = cache.get(download_key)
    if not download:
        return
    # Cap percentage between 0 and 100 and ensure it is an int
    download["percentage"] = min(max(0, int(percentage)), 100)
    cache.set(download_key, download, TIMEOUT)


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
