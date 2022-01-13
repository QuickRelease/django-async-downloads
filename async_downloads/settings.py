from django.conf import settings

DEFAULT_TIMEOUT = 60 * 60 * 24
DEFAULT_DOWNLOAD_TEMPLATE = "async_downloads/downloads.html"
DEFAULT_PATH_PREFIX = "downloads"
DEFAULT_COLLECTION_KEY_FORMAT = "async_downloads/{}"
DEFAULT_IN_MEMORY_MAX_SIZE_BYTES = 5 * 1e6  # Default of 5MB
DEFAULT_GAIA_MODE = False

TIMEOUT = getattr(settings, "ASYNC_DOWNLOADS_TIMEOUT", DEFAULT_TIMEOUT)
DOWNLOAD_TEMPLATE = getattr(settings, "ASYNC_DOWNLOADS_DOWNLOAD_TEMPLATE", DEFAULT_DOWNLOAD_TEMPLATE)
PATH_PREFIX = getattr(settings, "ASYNC_DOWNLOADS_PATH_PREFIX", DEFAULT_PATH_PREFIX)
COLLECTION_KEY_FORMAT = getattr(settings, "ASYNC_DOWNLOADS_COLLECTION_KEY_FORMAT", DEFAULT_COLLECTION_KEY_FORMAT)
IN_MEMORY_MAX_SIZE_BYTES = getattr(settings, "ASYNC_DOWNLOADS_IN_MEMORY_MAX_SIZE_BYTES", DEFAULT_IN_MEMORY_MAX_SIZE_BYTES)
GAIA_MODE = getattr(settings, "ASYNC_DOWNLOADS_GAIA_MODE", DEFAULT_GAIA_MODE)

if GAIA_MODE:
    DOWNLOAD_TEMPLATE = "async_downloads/gaia_downloads.html"
