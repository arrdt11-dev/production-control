from __future__ import annotations

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.repositories.batch import BatchRepository
from app.repositories.product import ProductRepository
from app.repositories.work_center import WorkCenterRepository


class UnitOfWork:
    """
    Unit of Work для async SQLAlchemy.

    Использование:
        async with UnitOfWork() as uow:
            ...
            await uow.commit()
    """

    def __init__(self) -> None:
        self.session: Optional[AsyncSession] = None
        self.work_centers: Optional[WorkCenterRepository] = None
        self.batches: Optional[BatchRepository] = None
        self.products: Optional[ProductRepository] = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = async_session()

        # репозитории
        self.work_centers = WorkCenterRepository(self.session)
        self.batches = BatchRepository(self.session)
        self.products = ProductRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if not self.session:
            return

        if exc:
            await self.session.rollback()
        else:
            # если забыли вызвать commit() — всё равно не фиксируем автоматически
            # (строже и предсказуемее)
            pass

        await self.session.close()

    async def commit(self) -> None:
        if not self.session:
            raise RuntimeError("UnitOfWork not started")
        await self.session.commit()

    async def rollback(self) -> None:
        if not self.session:
            raise RuntimeError("UnitOfWork not started")
        await self.session.rollback()
