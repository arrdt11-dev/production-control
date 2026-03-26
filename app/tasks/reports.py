import asyncio
from typing import Any

from app.celery_app import celery_app
from app.services.report_service import ReportService
from app.uow import UnitOfWork


async def _run_generate_report(batch_id: int) -> dict[str, Any]:
    async with UnitOfWork() as uow:
        return await ReportService.generate_batch_report(uow, batch_id)


@celery_app.task(name="generate_batch_report")
def generate_batch_report(batch_id: int) -> dict[str, Any]:
    try:
        return asyncio.run(_run_generate_report(batch_id))
    except Exception as e:
        return {
            "success": False,
            "batch_id": batch_id,
            "error": str(e),
        }