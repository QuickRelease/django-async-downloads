import os

from celery import shared_task
from django.core.cache import cache
from django.core.files.storage import default_storage

from async_downloads.settings import PATH_PREFIX


@shared_task()
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
