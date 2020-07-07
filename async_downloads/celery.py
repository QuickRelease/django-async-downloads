from celery import Celery
from celery.schedules import crontab

app = Celery("async_downloads")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.config.beat_schedule.update(
    {
        "async_downloads_cleanup": {
            "task": "tasks.cleanup_expired_downloads",
            "schedule": crontab(hour=0, minute=0, day_of_week=1)
        }
    }
)
