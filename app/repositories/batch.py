from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Batch


class BatchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, batch: Batch) -> Batch:
        self.session.add(batch)
        await self.session.flush()
        await self.session.refresh(batch)
        return batch

    async def list(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Batch]:
        result = await self.session.execute(
            select(Batch)
            .order_by(Batch.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get(self, batch_id: int) -> Batch | None:
        result = await self.session.execute(
            select(Batch).where(Batch.id == batch_id)
        )
        return result.scalar_one_or_none()

    async def update(self, batch: Batch, **kwargs) -> Batch:
        for key, value in kwargs.items():
            setattr(batch, key, value)

        await self.session.flush()
        await self.session.refresh(batch)
        return batch