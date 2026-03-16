from datetime import date

from fastapi import APIRouter, HTTPException, Query
from app.schemas.batch import BatchCreateIn, BatchRead, BatchUpdate
from app.services.batch_service import BatchService
from app.uow import UnitOfWork
import app.tasks.reports as reports

router = APIRouter(prefix="/api/v1/batches", tags=["Batches"])


@router.post("/", response_model=list[BatchRead], status_code=201)
async def create_batches(items: list[BatchCreateIn]):
    async with UnitOfWork() as uow:
        batches = await BatchService.create_batches(uow, items)
        return batches


@router.get("/", response_model=list[BatchRead])
async def list_batches(
    is_closed: bool | None = None,
    batch_number: int | None = None,
    batch_date: date | None = None,
    work_center_id: int | None = None,
    shift: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    async with UnitOfWork() as uow:
        batches = await BatchService.list_batches(
            uow=uow,
            is_closed=is_closed,
            batch_number=batch_number,
            batch_date=batch_date,
            work_center_id=work_center_id,
            shift=shift,
            offset=offset,
            limit=limit,
        )
        return batches


@router.get("/{batch_id}", response_model=BatchRead)
async def get_batch(batch_id: int):
    async with UnitOfWork() as uow:
        batch = await BatchService.get_batch(uow, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch


@router.patch("/{batch_id}", response_model=BatchRead)
async def update_batch(batch_id: int, data: BatchUpdate):
    async with UnitOfWork() as uow:
        batch = await BatchService.update_batch(uow, batch_id, data)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        return batch


@router.post("/{batch_id}/reports")
async def create_report(batch_id: int):
    task = reports.generate_batch_report.delay(batch_id)
    return {
        "task_id": task.id,
        "status": "PENDING",
    }