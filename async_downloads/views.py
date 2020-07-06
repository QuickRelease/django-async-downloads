import os

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.files.storage import default_storage
from django.http import JsonResponse, HttpResponse
from django.template.loader import render_to_string

from async_downloads.cache import get_collection_key
from async_downloads.settings import DOWNLOAD_TEMPLATE


@login_required
def ajax_update(request):
    download_keys = cache.get(get_collection_key(request.user.pk), [])
    downloads = []
    in_progress = False
    for i, download_key in enumerate(download_keys):
        dl = cache.get(download_key)
        if not dl:
            continue
        downloads.append(dl)
        if not dl["complete"]:
            in_progress = True
    # TODO: split up complete and in progress async_downloads?
    return JsonResponse(
        {
            "html": render_to_string(DOWNLOAD_TEMPLATE, {"downloads": downloads}),
            "downloads": downloads,
            "in_progress": in_progress,
        }
    )


@login_required
def ajax_clear_download(request):
    # TODO: consider just clearing the key without deleting,
    #  so that all deletion is done by one function
    filepath = request.POST.get("filepath")
    directory = os.path.split(filepath)[0]
    default_storage.delete(filepath)
    default_storage.delete(directory)
    download_key = os.path.split(directory)[1]
    cache.delete(download_key)
    return HttpResponse("")
