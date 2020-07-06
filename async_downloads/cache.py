import csv
from datetime import datetime
from io import StringIO
import os
import uuid

from django.core.cache import cache
from django.core.files.storage import default_storage

from async_downloads.settings import COLLECTION_KEY_FORMAT, PATH_PREFIX, TIMEOUT


def get_collection_key(pk):
    return COLLECTION_KEY_FORMAT.format(pk)


def init_download(pk, filename, name=None):
    download_key = f"{uuid.uuid4()}"
    filepath = os.path.join(PATH_PREFIX, download_key, filename)
    # TODO: consider inserting the collection key in here, so that it can be
    #  "touched" (`cache.touch`) to avoid the potential of the collection expiring
    #  before its downloads do
    download = {
        "timestamp": datetime.now(),
        "filepath": filepath,
        "name": name or filename,
        "complete": False,
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


def save_download(download_key, iterable):
    # TODO: make more generic (not just CSV support)
    output = StringIO(newline="")
    writer = csv.writer(output)
    for row in iterable:
        writer.writerow(row)
    download = cache.get(download_key)
    default_storage.save(download["filepath"], output)
    download["complete"] = True
    download["percentage"] = 100
    cache.set(download_key, download, TIMEOUT)


def set_percentage(download_key, percentage):
    download = cache.get(download_key)
    download["percentage"] = percentage
    cache.set(download_key, download, TIMEOUT)


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


def cleanup_expired_downloads():
    """
    Delete expired downloads (where the download no longer exists in the cache).
    This is a clean up operation to prevent downloads that weren't manually
    deleted from building up, and should be run periodically.
    """
    download_keys = default_storage.listdir(PATH_PREFIX)[0]
    for download_key in download_keys:
        if cache.get(download_key) is None:
            path = os.path.join(PATH_PREFIX, download_key)
            filepath = os.path.join(path, default_storage.listdir(path)[1][0])
            default_storage.delete(filepath)
            default_storage.delete(path)
