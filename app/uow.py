from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.repositories.batch import BatchRepository
from app.repositories.product import ProductRepository
from app.repositories.webhook import WebhookRepository
from app.repositories.work_center import WorkCenterRepository


class UnitOfWork:
    def __init__(self) -> None:
        self.session: AsyncSession | None = None
        self.batches: BatchRepository | None = None
        self.products: ProductRepository | None = None
        self.webhooks: WebhookRepository | None = None
        self.work_centers: WorkCenterRepository | None = None

    async def __aenter__(self) -> "UnitOfWork":
        self.session = async_session_maker()

        self.batches = BatchRepository(self.session)
        self.products = ProductRepository(self.session)
        self.webhooks = WebhookRepository(self.session)
        self.work_centers = WorkCenterRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        try:
            if self.session is not None:
                if exc_type is not None:
                    await self.session.rollback()
        finally:
            if self.session is not None:
                await self.session.close()

            self.session = None
            self.batches = None
            self.products = None
            self.webhooks = None
            self.work_centers = None

    async def commit(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")
        await self.session.commit()

    async def rollback(self) -> None:
        if self.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")
        await self.session.rollback()