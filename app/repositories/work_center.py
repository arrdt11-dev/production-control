from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkCenter


class WorkCenterRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_id(self, work_center_id: int) -> WorkCenter | None:
        return await self.session.get(WorkCenter, work_center_id)

    async def get_by_identifier(self, identifier: str) -> WorkCenter | None:
        return await self.session.scalar(select(WorkCenter).where(WorkCenter.identifier == identifier))

    async def create(self, identifier: str, name: str) -> WorkCenter:
        wc = WorkCenter(identifier=identifier, name=name)
        self.session.add(wc)
        return wc
