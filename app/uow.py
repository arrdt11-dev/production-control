from app.database import async_session
from app.repositories.batch import BatchRepository
from app.repositories.product import ProductRepository
from app.repositories.work_center import WorkCenterRepository
from app.repositories.webhook import WebhookRepository


class UnitOfWork:
    def __init__(self):
        self.session = None

        self.batches = None
        self.products = None
        self.work_centers = None
        self.webhooks = None

    async def __aenter__(self):
        self.session = async_session()

        self.batches = BatchRepository(self.session)
        self.products = ProductRepository(self.session)
        self.work_centers = WorkCenterRepository(self.session)
        self.webhooks = WebhookRepository(self.session)

        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc_type is not None and self.session is not None:
                await self.session.rollback()
        finally:
            if self.session is not None:
                await self.session.close()

    async def commit(self):
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        await self.session.commit()

    async def rollback(self):
        if self.session is None:
            raise RuntimeError("UnitOfWork session is not initialized")
        await self.session.rollback()