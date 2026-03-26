from fastapi import HTTPException, status
from sqlalchemy import func, select

from app.models import Batch
from app.schemas.batch import BatchCreate, BatchUpdate
from app.schemas.webhook import EventType
from app.services.webhook_service import WebhookService
from app.uow import UnitOfWork


class BatchService:
    @staticmethod
    def _build_batch(data: BatchCreate) -> Batch:
        return Batch(
            batch_number=data.batch_number,
            work_center_id=data.work_center_id,
            batch_date=data.batch_date,
            shift_start=data.shift_start,
            shift_end=data.shift_end,
            task_description=data.task_description,
            shift=getattr(data, "shift", "") or "",
            team=getattr(data, "team", "") or "",
            nomenclature=getattr(data, "nomenclature", "") or "",
            ekn_code=getattr(data, "ekn_code", "") or "",
            is_closed=False,
        )

    @staticmethod
    async def _get_batch_or_404(uow: UnitOfWork, batch_id: int) -> Batch:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        result = await uow.session.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        batch = result.scalar_one_or_none()

        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        return batch

    @staticmethod
    async def _create_batch_created_delivery(uow: UnitOfWork, batch: Batch) -> None:
        await WebhookService.create_event_deliveries(
            uow=uow,
            event_type=EventType.BATCH_CREATED,
            payload={
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "work_center_id": batch.work_center_id,
                "batch_date": str(batch.batch_date),
                "task_description": batch.task_description,
                "is_closed": batch.is_closed,
            },
        )

    @staticmethod
    async def create_batch(
        uow: UnitOfWork,
        data: BatchCreate,
    ) -> Batch:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        batch = BatchService._build_batch(data)

        uow.session.add(batch)
        await uow.session.flush()
        await uow.session.refresh(batch)

        await BatchService._create_batch_created_delivery(uow, batch)

        return batch

    @staticmethod
    async def create_batches(
        uow: UnitOfWork,
        items: list[BatchCreate],
    ) -> list[Batch]:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        created_batches: list[Batch] = []

        for item in items:
            batch = BatchService._build_batch(item)

            uow.session.add(batch)
            await uow.session.flush()
            await uow.session.refresh(batch)

            await BatchService._create_batch_created_delivery(uow, batch)
            created_batches.append(batch)

        await uow.commit()
        return created_batches

    @staticmethod
    async def get_batch(
        uow: UnitOfWork,
        batch_id: int,
    ) -> Batch:
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches is None")

        batch = await uow.batches.get(batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )
        return batch

    @staticmethod
    async def list_batches(
        uow: UnitOfWork,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[Batch], int]:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        result = await uow.session.execute(
            select(Batch).offset(offset).limit(limit)
        )
        batches = list(result.scalars().all())

        total_result = await uow.session.execute(
            select(func.count()).select_from(Batch)
        )
        total = total_result.scalar_one()

        return batches, total

    @staticmethod
    async def update_batch(
        uow: UnitOfWork,
        batch_id: int,
        data: BatchUpdate,
    ) -> Batch:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        batch = await BatchService._get_batch_or_404(uow, batch_id)

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(batch, field, value)

        await uow.commit()
        await uow.session.refresh(batch)
        return batch

    @staticmethod
    async def close_batch(
        uow: UnitOfWork,
        batch_id: int,
    ) -> Batch:
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        batch = await BatchService._get_batch_or_404(uow, batch_id)

        batch.is_closed = True
        await uow.session.flush()

        await WebhookService.create_event_deliveries(
            uow=uow,
            event_type=EventType.BATCH_CLOSED,
            payload={
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "is_closed": batch.is_closed,
            },
        )

        await uow.commit()
        await uow.session.refresh(batch)
        return batch