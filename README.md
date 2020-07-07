# Django Async Downloads

Asynchronous downloads scaffolding for Django projects.

- TODO: describe cache mechanism
- TODO: how to customise the front end

## Installation

In `requirements.txt`:
```
-e git+https://github.com/QuickRelease/django-async-downloads.git#egg=django-async-downloads
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

TODO: what needs to be done in `base.html`

## Usage

TODO: using the JS

### Cache Functions

#### `cache.init_download`
Initialise a download by preparing the cache entries. Returns a tuple of keys, the collection key
and specific download key. You would typically want to call this within the web process, and pass
the download key (and possibly the collection key) into the asynchronous function call so that the
status can be updated.

Arguments:
- `pk`: the unique identifier for a collection of downloads - this will typically be a user PK
- `filename`: the name of the file being downloaded (does not need to be unique)
- `name`: (optional) the name to associate with this download - defaults to `filename`


#### `cache.save_download`
The asynchronous process should call this function when the iterable is prepared in order to save
the output. The only supported format is CSV currently.

Arguments:
- `download_key`: the cache key of this particular download
- `iterable`: an iterable of data rows to be written


#### `cache.set_percentage`
The asynchronous process should call this function to update the completion percentage.

Arguments:
- `download_key`: the cache key of this particular download
- `percentage`: an integer between 0 and 100 (inclusive)


#### `cache.cleanup_collection`
There can be a build up of expired download keys in a collection so it can be worth periodically
removing them using this function. (Note that the collection cache itself will expire if not touched
for `ASYNC_DOWNLOADS_TIMEOUT` seconds, so it may not be critical to use this.)

Arguments:
- `collection_key`: the cache key of a collection of downloads


#### `cache.cleanup_expired_downloads`
Delete expired downloads (where the download no longer exists in the cache).
This is a clean up operation to prevent downloads that weren't manually deleted from building up,
and should be run periodically to avoid bloating the server with files.


## Configurable Settings

### `ASYNC_DOWNLOADS_TIMEOUT`
Default: `60 * 60 * 24`

### `ASYNC_DOWNLOADS_DOWNLOAD_TEMPLATE`
Default: `"download_items.html"`

### `ASYNC_DOWNLOADS_PATH_PREFIX`
Default: `"exports"`

### `ASYNC_DOWNLOADS_COLLECTION_KEY_FORMAT`
Default: `"async_downloads/{}"`
