import asyncio
import os
from datetime import datetime, UTC
from tempfile import NamedTemporaryFile

from app.celery_app import celery_app
from app.services.report_service import ReportService
from app.storage.minio_service import MinIOService
from app.uow import UnitOfWork
from app.settings import settings


async def _run_generate_report(
    batch_id: int,
    format: str = "excel",
    email: str | None = None,
) -> dict:
    if format not in {"excel", "xlsx"}:
        raise ValueError("Only excel reports are supported")

    async with UnitOfWork() as uow:
        batch = await uow.batches.get(batch_id)
        if not batch:
            raise ValueError(f"Batch with id={batch_id} not found")

        output, file_size = ReportService.generate_batch_report(batch)

    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    file_name = f"batch_{batch_id}_report_{timestamp}.xlsx"

    with NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(output.getvalue())
        temp_path = tmp.name

    minio = MinIOService()

    upload_result = minio.upload_file(
        bucket=settings.minio_bucket_reports,
        file_path=temp_path,
        object_name=file_name,
    )

    try:
        os.remove(temp_path)
    except Exception:
        pass

    result = ReportService.build_report_result(
        file_url=upload_result["file_url"],
        file_size=upload_result["file_size"],
    )

    result["success"] = True
    result["file_name"] = file_name

    return result


@celery_app.task(
    bind=True,
    max_retries=3,
    name="app.tasks.reports.generate_batch_report",
)
def generate_batch_report(
    self,
    batch_id: int,
    format: str = "excel",
    email: str | None = None,
) -> dict:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(
            _run_generate_report(batch_id, format, email)
        )
    except Exception:

        raise
    finally:
        try:
            loop.close()
        except Exception:
            pass