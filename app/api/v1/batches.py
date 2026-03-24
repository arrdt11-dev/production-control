import os
import tempfile
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

import app.tasks.aggregation as aggregation
import app.tasks.import_export as import_export
import app.tasks.reports as reports
from app.database import get_db
from app.schemas.analytics import BatchStatisticsResponse
from app.schemas.batch import (
    AggregateAsyncRequest,
    AggregateSyncRequest,
    BatchCreateIn,
    BatchExportRequest,
    BatchImportResponse,
    BatchRead,
    BatchUpdate,
)
from app.services.analytics_service import AnalyticsService
from app.services.batch_service import BatchService
from app.services.product_service import ProductService
from app.settings import settings
from app.storage.minio_service import MinIOService
from app.uow import UnitOfWork

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
        return await BatchService.list_batches(
            uow=uow,
            is_closed=is_closed,
            batch_number=batch_number,
            batch_date=batch_date,
            work_center_id=work_center_id,
            shift=shift,
            offset=offset,
            limit=limit,
        )


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



@router.post("/files/import", response_model=BatchImportResponse, status_code=202)
async def import_batches(file: UploadFile = File(...)):
    max_file_size = 10 * 1024 * 1024

    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in {".csv", ".xlsx", ".xls"}:
        raise HTTPException(status_code=400, detail="Only csv/xlsx/xls files are allowed")

    content = await file.read()
    if len(content) > max_file_size:
        raise HTTPException(status_code=400, detail="File too large (max 10MB)")

    minio = MinIOService()

    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    object_name = f"imports/{uuid4().hex}_{file.filename}"

    try:
        minio.upload_file(
            bucket=settings.minio_bucket_imports,
            file_path=tmp_path,
            object_name=object_name,
            expires_days=7,
        )
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    task = import_export.import_batches_from_file.delay(
        bucket=settings.minio_bucket_imports,
        object_name=object_name,
        user_id=None,
    )

    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "File uploaded, import started",
    }



@router.post("/files/export", status_code=202)
async def export_batches(body: BatchExportRequest):
    task = import_export.export_batches_to_file.delay(
        filters=body.filters.model_dump(exclude_none=True),
        format=body.format,
    )
    return {"task_id": task.id, "status": "PENDING"}


@router.post("/{batch_id}/reports")
async def create_report(batch_id: int):
    task = reports.generate_batch_report.delay(batch_id)
    return {"task_id": task.id, "status": "PENDING"}


@router.post("/{batch_id}/aggregate")
async def aggregate_products_sync(batch_id: int, body: AggregateSyncRequest):
    async with UnitOfWork() as uow:
        result = await ProductService.aggregate_sync(
            uow,
            batch_id,
            body.unique_codes,
        )
        if result.get("success") is False:
            raise HTTPException(status_code=404, detail=result.get("message"))
        return result


@router.post("/{batch_id}/aggregate-async")
async def aggregate_products_async(batch_id: int, body: AggregateAsyncRequest):
    task = aggregation.aggregate_products_batch.delay(
        batch_id,
        body.unique_codes,
    )
    return {
        "task_id": task.id,
        "status": "PENDING",
        "message": "Aggregation task started",
    }


@router.get("/{batch_id}/statistics", response_model=BatchStatisticsResponse)
async def get_batch_statistics(
    batch_id: int,
    session: AsyncSession = Depends(get_db),
):
    result = await AnalyticsService.get_batch_statistics(session, batch_id)
    if not result:
        raise HTTPException(status_code=404, detail=f"Batch with id={batch_id} not found")
    return result