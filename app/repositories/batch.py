from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Batch


class BatchRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, batch: Batch) -> None:
        self.session.add(batch)

    async def flush(self) -> None:
        await self.session.flush()

    async def create(self, data: Any = None, **kwargs) -> Batch:
        if data is not None and not kwargs:
            if isinstance(data, Batch):
                batch = data
            elif hasattr(data, "model_dump"):
                batch = Batch(**data.model_dump())
            elif isinstance(data, dict):
                batch = Batch(**data)
            else:
                raise TypeError(f"Unsupported data type for create(): {type(data)}")
        else:
            batch = Batch(**kwargs)

        self.session.add(batch)
        await self.session.flush()
        batch.products = []
        return batch

    async def get(self, batch_id: int) -> Batch | None:
        stmt = (
            select(Batch)
            .options(selectinload(Batch.products))
            .where(Batch.id == batch_id)
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
        stmt = select(Batch).options(selectinload(Batch.products)).order_by(Batch.id.desc())

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

        stmt = stmt.offset(offset).limit(limit)

        res = await self.session.execute(stmt)
        return list(res.scalars().all())
