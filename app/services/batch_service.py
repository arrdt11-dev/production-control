from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.models import Batch, Product
from app.schemas.batch import BatchCreateIn, BatchUpdate
from app.uow import UnitOfWork


class BatchService:
    @staticmethod
    async def create_batches(uow: UnitOfWork, items: list[BatchCreateIn]) -> list[Batch]:
        assert uow.work_centers and uow.batches

        created: list[Batch] = []

        for it in items:
            wc = await uow.work_centers.get_by_identifier(it.work_center_identifier)
            if not wc:
                wc = await uow.work_centers.create(
                    identifier=it.work_center_identifier,
                    name=it.work_center_name,
                )

            batch = Batch(
                is_closed=it.is_closed,
                closed_at=(datetime.now(timezone.utc) if it.is_closed else None),
                task_description=it.task_description,
                work_center_id=wc.id,  # после flush будет
                shift=it.shift,
                team=it.team,
                batch_number=it.batch_number,
                batch_date=it.batch_date,
                nomenclature=it.nomenclature,
                ekn_code=it.ekn_code,
                shift_start=it.shift_start,
                shift_end=it.shift_end,
            )
            await uow.batches.create(batch)
            created.append(batch)

        try:
            await uow.commit()
        except IntegrityError:
            await uow.rollback()
            raise

        # refresh ids
        assert uow.session
        for b in created:
            await uow.session.refresh(b)
        return created

    @staticmethod
    async def get_batch(uow: UnitOfWork, batch_id: int) -> Batch | None:
        assert uow.batches
        return await uow.batches.get_by_id_with_products(batch_id)

    @staticmethod
    async def update_batch(uow: UnitOfWork, batch_id: int, data: BatchUpdate) -> Batch | None:
        assert uow.batches
        batch = await uow.batches.get_by_id(batch_id)
        if not batch:
            return None

        # PATCH поля
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(batch, field, value)

        # Правила ТЗ по closed_at
        if "is_closed" in data.model_dump(exclude_unset=True):
            if batch.is_closed:
                batch.closed_at = datetime.now(timezone.utc)
            else:
                batch.closed_at = None

        await uow.commit()
        assert uow.session
        await uow.session.refresh(batch)
        return batch

    @staticmethod
    async def list_batches(
        uow: UnitOfWork,
        is_closed: bool | None,
        batch_number: int | None,
        batch_date,
        work_center_id: int | None,
        shift: str | None,
        offset: int,
        limit: int,
    ) -> list[Batch]:
        assert uow.batches
        return await uow.batches.list(is_closed, batch_number, batch_date, work_center_id, shift, offset, limit)
