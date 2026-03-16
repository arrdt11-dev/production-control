import asyncio
import os
import tempfile
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models import Batch
from app.repositories.webhook import WebhookRepository
from app.services.report_service import ReportService
from app.services.webhook_service import WebhookService
from app.settings import settings
from app.storage.minio_service import MinIOService
from app.tasks.webhooks import send_webhook_delivery


async def generate_report_async(batch_id: int):
    async with async_session() as db:
        result = await db.execute(
            select(Batch)
            .options(selectinload(Batch.products))
            .where(Batch.id == batch_id)
        )
        batch = result.scalar_one_or_none()

        if not batch:
            return {
                "success": False,
                "error": f"Batch with id={batch_id} not found",
            }

        file_stream, file_size = ReportService.generate_batch_report(batch)

        storage = MinIOService()
        file_name = f"batch_{batch_id}_report.xlsx"

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
                tmp.write(file_stream.getvalue())
                temp_path = tmp.name

            upload_result = storage.upload_file(
                settings.minio_bucket_reports,
                temp_path,
                file_name,
            )

            expires_at = datetime.now(UTC) + timedelta(hours=24)

            payload = WebhookService.build_report_generated_payload(
                batch_id=batch_id,
                report_type="excel",
                file_url=upload_result["file_url"],
                expires_at=expires_at.isoformat(),
            )

            webhook_repo = WebhookRepository(db)
            subs_result = await db.execute(
                select_batch_created_subscriptions_sql()
            ) if False else None  # no-op placeholder

            deliveries = []
            subscriptions, _ = await webhook_repo.list_subscriptions(offset=0, limit=1000)
            for sub in subscriptions:
                if not sub.is_active:
                    continue
                if "report_generated" not in sub.events:
                    continue

                delivery = await webhook_repo.create_delivery(
                    subscription_id=sub.id,
                    event_type="report_generated",
                    payload=payload,
                    status="pending",
                    attempts=0,
                )
                deliveries.append(delivery)

            await db.commit()

            for delivery in deliveries:
                send_webhook_delivery.delay(delivery.id)

            return {
                "success": True,
                "file_url": upload_result["file_url"],
                "file_name": file_name,
                "file_size": file_size,
                "expires_at": expires_at.isoformat(),
            }
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)


@shared_task(bind=True)
def generate_batch_report(self, batch_id: int):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(generate_report_async(batch_id))
    loop.close()
    return result
