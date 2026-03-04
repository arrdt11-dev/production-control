from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Batch


class BatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(self, batch: Batch) -> Batch:
        self.session.add(batch)
        await self.session.flush()
        return batch

    async def get_by_id(self, batch_id: int) -> Batch | None:
        return await self.session.get(Batch, batch_id)

    async def get_by_id_with_products(self, batch_id: int) -> Batch | None:
        stmt = (
            select(Batch)
            .where(Batch.id == batch_id)
            .options(selectinload(Batch.products))
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def list(
        self,
        is_closed: bool | None,
        batch_number: int | None,
        batch_date: date | None,
        work_center_id: int | None,
        shift: str | None,
        offset: int,
        limit: int,
    ) -> list[Batch]:
        stmt = select(Batch)

        if is_closed is not None:
            stmt = stmt.where(Batch.is_closed == is_closed)
        if batch_number is not None:
            stmt = stmt.where(Batch.batch_number == batch_number)
        if batch_date is not None:
            stmt = stmt.where(Batch.batch_date == batch_date)
        if work_center_id is not None:
            stmt = stmt.where(Batch.work_center_id == work_center_id)
        if shift is not None:
            stmt = stmt.where(Batch.shift == shift)

        stmt = stmt.order_by(Batch.id.desc()).offset(offset).limit(limit)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())