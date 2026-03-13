import os
from datetime import datetime, timedelta, UTC

from celery import shared_task
from sqlalchemy import select

from app.database import async_session
from app.models import Batch
from app.services.report_service import ReportService
from app.storage.minio_service import MinIOService


@shared_task
def generate_batch_report(batch_id: int):

    import asyncio

    async def run():
        async with async_session() as db:

            result = await db.execute(
                select(Batch).where(Batch.id == batch_id)
            )

            batch = result.scalar_one_or_none()

            if not batch:
                return {
                    "success": False,
                    "error": f"Batch with id={batch_id} not found",
                }

            # генерация excel
            file_stream, file_size = ReportService.generate_batch_report(batch)

            # загрузка в MinIO
            storage = MinIOService()

            file_name = f"batch_{batch_id}.xlsx"

            file_url = storage.upload_file(
                bucket="reports",
                file=file_stream,
                file_name=file_name,
            )

            expires_at = datetime.now(UTC) + timedelta(hours=24)

            return {
                "success": True,
                "file_url": file_url,
                "file_size": file_size,
                "expires_at": expires_at.isoformat(),
            }

    return asyncio.run(run())