from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.schemas.batch import BatchCreate
from app.schemas.webhook import EventType


class BatchService:
    @staticmethod
    async def create_batch(uow, data: BatchCreate):
        if uow.work_centers is None or uow.batches is None or uow.webhooks is None:
            raise RuntimeError("UnitOfWork repositories are not initialized")

        work_center = await uow.work_centers.get(data.work_center_id)
        if not work_center:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work center with id={data.work_center_id} not found",
            )

        batch = await uow.batches.create(data)

        await uow.webhooks.create_event_deliveries(
            event_type=EventType.batch_created,
            payload={
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "work_center_id": batch.work_center_id,
                "planned_quantity": batch.planned_quantity,
                "status": batch.status,
            },
        )

        await uow.commit()
        return batch

    @staticmethod
    async def create_batches(uow, items: list[BatchCreate]):
        if uow.session is None:
            raise RuntimeError("UnitOfWork.session is not initialized")

        created_batches = []

        for item in items:
            work_center = await uow.work_centers.get(item.work_center_id)
            if not work_center:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Work center with id={item.work_center_id} not found",
                )

            batch = await uow.batches.create(item)
            created_batches.append(batch)

        await uow.commit()
        return created_batches

    @staticmethod
    async def get_all_batches(uow):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")
        return await uow.batches.list(
            is_closed=None,
            batch_number=None,
            batch_date=None,
            work_center_id=None,
            shift=None,
            offset=0,
            limit=100,
        )

    @staticmethod
    async def get_batch(uow, batch_id: int):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")

        batch = await uow.batches.get(batch_id, with_products=True)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )
        return batch

    @staticmethod
    async def update_batch(uow, batch_id: int, data):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")

        batch = await uow.batches.get(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        payload = data.model_dump(exclude_none=True)
        for key, value in payload.items():
            setattr(batch, key, value)

        await uow.commit()
        return batch

    @staticmethod
    async def list_batches(
        uow,
        is_closed: bool | None,
        batch_number: int | None,
        batch_date,
        work_center_id: int | None,
        shift: str | None,
        offset: int,
        limit: int,
    ):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")

        return await uow.batches.list(
            is_closed=is_closed,
            batch_number=batch_number,
            batch_date=batch_date,
            work_center_id=work_center_id,
            shift=shift,
            offset=offset,
            limit=limit,
        )

    @staticmethod
    async def start_batch(uow, batch_id: int):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")

        batch = await uow.batches.get(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        if batch.started_at is None:
            batch.started_at = datetime.now(timezone.utc)

        batch.status = "in_progress"

        await uow.commit()
        return batch

    @staticmethod
    async def complete_batch(uow, batch_id: int):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")

        batch = await uow.batches.get(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        if batch.started_at is None:
            batch.started_at = datetime.now(timezone.utc)

        batch.completed_at = datetime.now(timezone.utc)
        batch.status = "completed"

        await uow.commit()
        return batch

    @staticmethod
    async def get_batch_statistics(uow, batch_id: int):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork.batches is not initialized")

        batch = await uow.batches.get(batch_id, with_products=True)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        total_products = len(batch.products)
        aggregated_products = sum(1 for product in batch.products if product.is_aggregated)
        progress = (aggregated_products / total_products * 100) if total_products > 0 else 0

        duration_seconds = None
        if batch.started_at and batch.completed_at:
            duration_seconds = (batch.completed_at - batch.started_at).total_seconds()

        return {
            "batch_id": batch.id,
            "batch_number": batch.batch_number,
            "status": batch.status,
            "planned_quantity": batch.planned_quantity,
            "total_products": total_products,
            "aggregated_products": aggregated_products,
            "progress_percent": round(progress, 2),
            "started_at": batch.started_at,
            "completed_at": batch.completed_at,
            "duration_seconds": duration_seconds,
        }