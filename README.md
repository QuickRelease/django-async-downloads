# Django Async Downloads

Asynchronous downloads scaffolding for Django projects.

- TODO: describe cache mechanism
- TODO: how to customise the front end

## Installation

```
# Without websocket support
pip install django-async-downloads

# With Websocket support
pip install django-async-downloads[ws]
```

Note at the present time on Windows, if you require websocket support,
you will need "Microsoft Visual C++ 14.0" installed (https://visualstudio.microsoft.com/visual-cpp-build-tools/) 
due to `hiredis` from the dependency chain (`channels_redis` -> `aioredis-py` -> `hiredis`).

Add to your `INSTALLED_APPS`:
```
INSTALLED_APPS = [
    ...
    "async_downloads",
]
```

Add to your project's `url_patterns`:
```
path("async_downloads/", include("async_downloads.urls"))
```

Add the CSS:
```
<link rel="stylesheet" type="text/css" href="{% static 'css/async_downloads.css' %}" />
```

Add the JS:
```
<script src="{% static "js/async_downloads.js" %}" id="async-downloads-script"
    data-url="{% url 'async_downloads:ajax_update' %}"
    data-clear-url="{% url 'async_downloads:ajax_clear_download' %}"></script>
```

Include the download centre nav-menu:
```
<ul class="navbar-nav">
    ...
    {% include 'async_downloads/download_centre.html' %}
    ...
```

## WS mode
Package can be used with websockets to provide asynchronous communication
between frontend and backend.
If package will be used in websockets mode additional settings must be applied.
* Inside common settings `WS_MODE` must be toggled on.
    ```
    ASYNC_DOWNLOADS_WS_MODE = True
    ```
* Application needs to be configured as a `ASGI` and proper WS urls need to be configured:
    ```
    # ws/urls.py
    from async_downloads.ws_consumers import DownloadsConsumer
     
     urlpatterns += [
        re_path(r"ws/downloads/(?P<username>[\w.]+)/$", DownloadsConsumer.as_asgi()),
     ]
    ```
    ```
    # example asgi.py
    from django.core.asgi import get_asgi_application

    from channels.auth import AuthMiddlewareStack
    from channels.routing import ProtocolTypeRouter, URLRouter

    import ws.urls

    application = ProtocolTypeRouter(
        {
            "http": get_asgi_application(),
            "websocket": AuthMiddlewareStack(URLRouter(ws.urls.urlpatterns)),
        }
    )
    ```

* Change in application template async-downloads section to use WS js version.
    ```
    # example: FULL_WS_URL = "http://app.com/ws/downloads/"
    <script src="{% static "js/ws_async_downloads.js" %}" id="async-downloads-script"
        data-url="{{ FULL_WS_URL }}"
    </script>
    ```
    - `data-url` must be an absolute URL because this is required for a WebSocket connection,
        and it must include the protocol because the `ws_async_downloads.js` script will 
        inspect it to determine which WebSockets protocol to use - `ws` if `http` or `wss` 
        if `https`.

* Configure `CHANNEL_LAYERS` inside common settings. Example config:
    ```
    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "channels_redis.core.RedisChannelLayer",
            "CONFIG": {
                "hosts": [("127.0.0.1", 6379)],
            },
        },
    }
    ```

## Usage

TODO: using the JS

### Cache Functions

#### `cache.init_download`
Initialise a download by preparing the cache entries. Returns a tuple of keys, the collection key
and specific download key. You would typically want to call this within the web process, and pass
the download key (and possibly the collection key) into the asynchronous function call so that the
status can be updated.

Arguments:
- `user`: the unique identifier for a collection of downloads - this will typically be a user
         object but can be user PK or username.
- `filename`: the name of the file being downloaded (does not need to be unique)
- `name`: (optional) the name to associate with this download - defaults to `filename`


#### `cache.save_download`
The asynchronous process should call this function when the iterable or file is prepared in order to save
the output.

Arguments:
- `download_key`: the cache key of this particular download
- `iterable`: (optional) an iterable of data rows to be written
- `file`: (optional) a BytesIO object


#### `cache.update_percentage`
The asynchronous process can call this function to calculate and update the completion percentage.
(download_key, total, cur, resolution=10):
Arguments:
- `download_key`: the cache key of this particular download
- `total`: total to compare current progress against
- `cur`: current progress index
- `resolution`: resolution of the percentage calculation (make smaller for fewer updates, larger for
more precision); default is `10`, meaning it will increase in steps of 10%. The value is capped between
`1` and `100`.


#### `cache.set_percentage`
The asynchronous process can call this function to directly set the completion percentage.

Arguments:
- `download_key`: the cache key of this particular download
- `percentage`: an number between 0 and 100 (inclusive)


#### `cache.cleanup_collection`
There can be a build up of expired download keys in a collection so it can be worth periodically
removing them using this function. (Note that the collection cache itself will expire if not touched
for `ASYNC_DOWNLOADS_TIMEOUT` seconds, so it may not be critical to use this.)

Arguments:
- `collection_key`: the cache key of a collection of downloads


### `cache.set_error`
The asynchronous process can call this function to set an error message on the download.

Arguments:
- `download_key`: the cache key of this particular download
- `error`: the error message to set

#### `tasks.cleanup_expired_downloads`
Delete expired downloads (where the download no longer exists in the cache).
This is a clean up operation to prevent downloads that weren't manually deleted from building up,
and should be run periodically to avoid bloating the server with files.

This is best setup as a periodic task in your project, which can be done by adding the following
to your project's `celery.py`:
```
app.conf.beat_schedule = {
    "async_downloads_cleanup": {
        "task": "async_downloads.tasks.cleanup_expired_downloads",
        "schedule": crontab(hour=0, minute=0, day_of_week=1)
    }
}
```

## Configurable Settings

### `ASYNC_DOWNLOADS_TIMEOUT`
Default: `60 * 60 * 24` (1 day)

This is the cache timeout used for cache operations. 

### `ASYNC_DOWNLOADS_DOWNLOAD_TEMPLATE`
Default: `"async_downloads/downloads.html"`

This is the template that will be used by the `ajax_update` view. You can override it by creating
a template in `<project>/templates/async_downloads/downloads.html`, or else putting the template
wherever you choose and changing this setting.

### `ASYNC_DOWNLOADS_PATH_PREFIX`
Default: `"downloads"`

The parent directory for all downloads in the `MEDIA_ROOT` directory.

### `ASYNC_DOWNLOADS_COLLECTION_KEY_FORMAT`
Default: `"async_downloads/{}"`

The collection key keeps track of the cache keys of a grouped collection of downloads. In the
unlikely event that this key format clashes with something in your project, you can change it.
The expectation is for the string to have a user primary key inserted with `str.format`, so `{}`
is required to be present.

### `ASYNC_DOWNLOADS_WS_CHANNEL_NAME`
Default: `"downloads"`

The channel name for all shared information about download in channels cache layer.

### `ASYNC_DOWNLOADS_CACHE_NAME`

If this settings will be added default cache will be changed into new with provided name.

### `ASYNC_DOWNLOADS_WS_MODE`
Default: `False`

If this flag will be set to `True` package will be set to work with WebSockets in [WS_MODE](#ws-mode).

### `ASYNC_DOWNLOADS_CSS_CLASS`
Default: `None`

Additional CSS class can be added to `download-content` div.
