import asyncio

from app.celery_app import celery_app
from app.database import async_session
from app.repositories.webhook import WebhookRepository
from app.tasks.webhooks import send_webhook_delivery


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
    return asyncio.run(_retry_failed_webhooks_async())


async def _retry_failed_webhooks_async():
    async with async_session() as session:
        repo = WebhookRepository(session)
        failed_deliveries = await repo.list_failed_deliveries(limit=100)

        retried = 0
        total = len(failed_deliveries)

        for delivery in failed_deliveries:
            subscription = delivery.subscription

            if not subscription:
                continue

            if not subscription.is_active:
                continue

            # если лимит уже достигнут — больше не ретраим
            if delivery.attempts >= subscription.retry_count:
                continue

            send_webhook_delivery.delay(delivery.id)
            retried += 1

        return {
            "success": True,
            "retried": retried,
            "total": total,
        }