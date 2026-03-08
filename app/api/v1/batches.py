from __future__ import annotations

from datetime import date
from fastapi import APIRouter, HTTPException, Query

from app.schemas import BatchCreateIn, BatchRead, BatchUpdate, AggregateSyncRequest
from app.services.batch_service import BatchService
from app.services.product_service import ProductService
from app.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/batches", tags=["Batches"])


def batch_to_dict(b):
    return {
        "id": b.id,
        "is_closed": b.is_closed,
        "closed_at": b.closed_at,
        "task_description": b.task_description,
        "work_center_id": b.work_center_id,
        "shift": b.shift,
        "team": b.team,
        "batch_number": b.batch_number,
        "batch_date": b.batch_date,
        "nomenclature": b.nomenclature,
        "ekn_code": b.ekn_code,
        "shift_start": b.shift_start,
        "shift_end": b.shift_end,
        "products": [],
    }


@router.post("", response_model=list[BatchRead], status_code=201)
async def create_batches(items: list[BatchCreateIn]):
    async with UnitOfWork() as uow:
        created = await BatchService.create_batches(uow, items)
        return [batch_to_dict(b) for b in created]


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


@router.get("", response_model=list[BatchRead])
async def list_batches(
    is_closed: bool | None = None,
    batch_number: int | None = None,
    batch_date: date | None = None,
    work_center_id: int | None = None,
    shift: str | None = None,
    offset: int = 0,
    limit: int = Query(default=20, ge=1, le=100),
):
    async with UnitOfWork() as uow:
        return await BatchService.list_batches(
            uow, is_closed, batch_number, batch_date, work_center_id, shift, offset, limit
        )


@router.post("/{batch_id}/aggregate")
async def aggregate_products_sync(batch_id: int, body: AggregateSyncRequest):
    async with UnitOfWork() as uow:
        result = await ProductService.aggregate_sync(uow, batch_id, body.unique_codes)
        if result.get("success") is False:
            raise HTTPException(status_code=404, detail=result.get("message", "Batch not found"))
        return result

from pydantic import BaseModel
from app.tasks.aggregation import aggregate_products_batch


class AggregateAsyncRequest(BaseModel):
    unique_codes: list[str]


@router.post("/{batch_id}/aggregate-async", status_code=202)
async def aggregate_products_async(batch_id: int, body: AggregateAsyncRequest):
    task = aggregate_products_batch.delay(batch_id=batch_id, unique_codes=body.unique_codes)
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "Aggregation task started",
    }

