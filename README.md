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


#### `tasks.cleanup_expired_downloads`
Delete expired downloads (where the download no longer exists in the cache).
This is a clean up operation to prevent downloads that weren't manually deleted from building up,
and should be run periodically to avoid bloating the server with files.

This is best setup as a periodic task in your project.


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
