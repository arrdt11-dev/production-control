from celery import Celery
from celery.schedules import crontab

from app.settings import settings

celery_app = Celery(
    "production_control",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.aggregation",
        "app.tasks.scheduled",
    ],
)

celery_app.conf.update(
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    result_expires=3600 * 24,
    beat_schedule={
        "auto-close-expired-batches": {
            "task": "app.tasks.scheduled.auto_close_expired_batches",
            "schedule": crontab(hour=1, minute=0),
        },
        "cleanup-old-files": {
            "task": "app.tasks.scheduled.cleanup_old_files",
            "schedule": crontab(hour=2, minute=0),
        },
        "update-statistics": {
            "task": "app.tasks.scheduled.update_cached_statistics",
            "schedule": crontab(minute="*/5"),
        },
        "retry-failed-webhooks": {
            "task": "app.tasks.scheduled.retry_failed_webhooks",
            "schedule": crontab(minute="*/15"),
        },
    },
)