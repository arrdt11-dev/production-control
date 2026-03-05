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
