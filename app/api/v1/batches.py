from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.database import async_session
from app.models import Batch
import app.tasks.reports as reports

router = APIRouter(prefix="/api/v1/batches", tags=["Batches"])


@router.get("/")
async def list_batches():
    async with async_session() as db:
        result = await db.execute(
            select(Batch).options(selectinload(Batch.products))
        )
        batches = result.scalars().all()
        return batches


@router.get("/{batch_id}")
async def get_batch(batch_id: int):
    async with async_session() as db:
        result = await db.execute(
            select(Batch)
            .where(Batch.id == batch_id)
            .options(selectinload(Batch.products))
        )
        batch = result.scalar_one_or_none()

        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        return batch


@router.post("/{batch_id}/reports")
async def create_report(batch_id: int):
    task = reports.generate_batch_report.delay(batch_id)

    return {
        "task_id": task.id,
        "status": "PENDING"
    }