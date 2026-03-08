from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkCenter


class WorkCenterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add(self, wc: WorkCenter) -> None:
        self.session.add(wc)

    async def flush(self) -> None:
        await self.session.flush()

    async def create(self, data=None, **kwargs) -> WorkCenter:
        if data is not None and not kwargs:
            if isinstance(data, WorkCenter):
                wc = data
            elif hasattr(data, "model_dump"):
                wc = WorkCenter(**data.model_dump())
            elif isinstance(data, dict):
                wc = WorkCenter(**data)
            else:
                raise TypeError(f"Unsupported data type for create(): {type(data)}")
        else:
            wc = WorkCenter(**kwargs)

        self.session.add(wc)
        await self.session.flush()
        return wc

    async def get(self, wc_id: int) -> WorkCenter | None:
        return await self.session.get(WorkCenter, wc_id)

    async def get_by_identifier(self, identifier: str) -> WorkCenter | None:
        res = await self.session.execute(
            select(WorkCenter).where(WorkCenter.identifier == identifier)
        )
        return res.scalar_one_or_none()

    async def list(self) -> list[WorkCenter]:
        res = await self.session.execute(select(WorkCenter).order_by(WorkCenter.id))
        return list(res.scalars().all())