from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import WorkCenter


class WorkCenterRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, work_center: WorkCenter) -> WorkCenter:
        self.session.add(work_center)
        await self.session.flush()
        await self.session.refresh(work_center)
        return work_center

    async def list(self) -> list[WorkCenter]:
        result = await self.session.execute(
            select(WorkCenter).order_by(WorkCenter.id)
        )
        return list(result.scalars().all())

    async def get(self, work_center_id: int) -> WorkCenter | None:
        result = await self.session.execute(
            select(WorkCenter).where(WorkCenter.id == work_center_id)
        )
        return result.scalar_one_or_none()

    async def update(self, work_center: WorkCenter, **kwargs) -> WorkCenter:
        for key, value in kwargs.items():
            setattr(work_center, key, value)

        await self.session.flush()
        await self.session.refresh(work_center)
        return work_center