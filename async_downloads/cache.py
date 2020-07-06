import csv
from datetime import datetime
from io import StringIO
import os
import uuid

from django.core.cache import cache
from django.core.files.storage import default_storage

from async_downloads.settings import USER_KEY_FORMAT, PATH_PREFIX, TIMEOUT


def get_user_key(user):
    return USER_KEY_FORMAT.format(user.pk)


def init_download(user, filename, name):
    download_key = f"{uuid.uuid4()}"
    filepath = os.path.join(PATH_PREFIX, download_key, filename)
    download = {
        "timestamp": datetime.now(),
        "filepath": filepath,
        "name": name,
        "complete": False,
        "percentage": 0,
    }
    user_key = get_user_key(user)
    # TODO: locking mechanism - consider https://pypi.org/project/django-cache-lock/
    # TODO: build the cleanup of expired keys into this?
    #  (since we are already modifying the cache entry)
    download_keys = [download_key] + cache.get(user_key, [])
    cache.set(user_key, download_keys, TIMEOUT)
    cache.set(download_key, download, TIMEOUT)
    return user_key, download_key


def save_download(download_key, iterable):
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


def cleanup_user_downloads(user_key):
    # TODO: clean up files
    #  need to delete the file first, then the directory
    #    default_storage.delete(f for f in default_storage.listdir(os.path.join(PATH_PREFIX, download_key)))
    #    default_storage.delete(os.path.join(PATH_PREFIX, download_key))
    stored_keys = cache.get(user_key, [])
    active_keys = [key for key in stored_keys if cache.get(key) is not None]
    # Avoid cache write if possible to reduce chance of clobbering
    if len(active_keys) != len(stored_keys):
        cache.set(user_key, active_keys)
    # cache.set(
    #     user_key, [key for key in cache.get(user_key, []) if cache.get(key) is not None]
    # )


def cleanup_expired_downloads():
    """
    Delete expired async_downloads (where the download no longer exists in the cache).
    This is a clean up operation to prevent async_downloads that weren't manually
    deleted from building up, and should be run periodically.
    """
    download_keys = default_storage.listdir(PATH_PREFIX)[0]
    for download_key in download_keys:
        if cache.get(download_key) is None:
            path = os.path.join(PATH_PREFIX, download_key)
            filepath = os.path.join(path, default_storage.listdir(path)[1][0])
            default_storage.delete(filepath)
            default_storage.delete(path)
