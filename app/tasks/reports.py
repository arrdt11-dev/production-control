import asyncio
import os
import tempfile
from datetime import datetime, timedelta, UTC

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models import Batch
from app.services.report_service import ReportService
from app.storage.minio_service import MinIOService


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

            file_url = storage.upload_file(
                "reports",
                temp_path,
                file_name,
            )

            expires_at = datetime.now(UTC) + timedelta(hours=24)

            return {
                "success": True,
                "file_url": file_url,
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