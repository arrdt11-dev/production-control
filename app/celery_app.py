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
        "app.tasks.reports",
        "app.tasks.import_export",
        "app.tasks.webhooks",
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
        "retry-failed-webhooks": {
            "task": "app.tasks.scheduled.retry_failed_webhooks",
            "schedule": crontab(minute="*/15"),
        },
    },
)