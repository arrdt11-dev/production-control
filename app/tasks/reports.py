import asyncio
from openpyxl import Workbook

from app.celery_app import celery_app
from app.storage.minio_service import MinIOService
from app.uow import UnitOfWork


async def _get_batch(batch_id: int):
    async with UnitOfWork() as uow:
        return await uow.batches.get_by_id(batch_id)


def build_excel(batch):
    wb = Workbook()
    ws = wb.active

    ws.append(["Batch ID", batch.id])
    ws.append(["Batch number", batch.batch_number])
    ws.append(["Date", str(batch.batch_date)])
    ws.append(["Shift", batch.shift])
    ws.append(["Team", batch.team])

    file_path = f"/tmp/batch_{batch.id}.xlsx"
    wb.save(file_path)

    return file_path


@celery_app.task
def generate_batch_report(batch_id: int):

    batch = asyncio.run(_get_batch(batch_id))

    file_path = build_excel(batch)

    storage = MinIOService()

    file_url = storage.upload_file(
        "reports",
        file_path,
        f"batch_{batch_id}.xlsx",
    )

    return {
        "success": True,
        "file_url": file_url,
        "file_name": f"batch_{batch_id}.xlsx",
    }