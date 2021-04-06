from typing import Callable, Iterable, Union

from django.contrib.auth.models import AbstractBaseUser
from django.db.models import QuerySet
from django.utils import timezone

from celery import Task

from .cache import init_download, save_download, update_percentage

__all__ = (
    "init_generic_csv_download",
    "queryset_to_csv",
)


def queryset_to_csv(
    download_key: str, header: Iterable[str], queryset: QuerySet, row_function: Callable
):
    """Save a QuerySet to an initialised csv, applying the `row_function` callable to
    each QuerySet row to generate the export line

    Example:
    ```
    from async_downloads.shortcuts import queryset_to_csv

    @task
    def export_task(download_key):
        def export_book(book):
            return [book.pk, book.title, book.author_id]

        queryset_to_csv(
            download_key,
            ["ID", "Title", "Author ID"],
            Book.objects.all(),
            export_book,
        )
    ```
    """
    if not isinstance(queryset, QuerySet):
        raise ValueError(
            "Third argument to queryset_to_csv must be a QuerySet, not '%s'."
            % queryset.__class__.__name__
        )

    total = len(queryset)

    def _generate_data():
        yield header

        for row, obj in enumerate(queryset):
            update_percentage(download_key, total, row)
            yield row_function(obj)

    save_download(download_key, _generate_data())


def init_generic_csv_download(
    task: Task, user: Union[AbstractBaseUser, int], name: str, *task_args, **task_kwargs
):
    """`init_download` helper with some sensible defaults for filename and display name,
    appending a modified ISO-8601 timestamp"""
    if isinstance(user, AbstractBaseUser):
        user_id = user.pk
    else:
        user_id = user

    timestamp = timezone.now()

    filename = f"{name.replace(' ', '_')}_{timestamp.strftime('%Y-%m-%d_%H-%M')}.csv"

    collection_key, download_key = init_download(
        user_id, filename, f"{name} {timestamp.strftime('%Y-%m-%d')}"
    )

    task.delay(download_key, *task_args, **task_kwargs)

    return collection_key, download_key
