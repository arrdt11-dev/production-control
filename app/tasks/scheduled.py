from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.celery_app import celery_app
from app.models import WebhookDelivery
from app.tasks.webhooks import get_sync_session_local, send_webhook_delivery


@celery_app.task
def auto_close_expired_batches():
    return {"success": True, "message": "scheduled task placeholder"}


@celery_app.task
def cleanup_old_files():
    return {"success": True, "message": "scheduled task placeholder"}


@celery_app.task
def update_cached_statistics():
    return {"success": True, "message": "scheduled task placeholder"}


@celery_app.task
def retry_failed_webhooks():
    db = get_sync_session_local()()

    try:
        failed_deliveries = list(
            db.execute(
                select(WebhookDelivery)
                .options(selectinload(WebhookDelivery.subscription))
                .where(WebhookDelivery.status == "failed")
                .limit(100)
            ).scalars().all()
        )

        retried = 0
        total = len(failed_deliveries)

        for delivery in failed_deliveries:
            subscription = delivery.subscription

            if subscription is None:
                continue

            if not subscription.is_active:
                continue

            if delivery.attempts >= subscription.retry_count:
                continue

            send_webhook_delivery.delay(delivery.id)
            retried += 1

        return {
            "success": True,
            "retried": retried,
            "total": total,
        }
    finally:
        db.close()