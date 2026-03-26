from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import WebhookDelivery, WebhookSubscription


class WebhookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_subscription(
        self,
        subscription: WebhookSubscription,
    ) -> WebhookSubscription:
        self.session.add(subscription)
        await self.session.flush()
        await self.session.refresh(subscription)
        return subscription

    async def get_subscription(self, subscription_id: int) -> WebhookSubscription | None:
        result = await self.session.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def list_subscriptions(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[WebhookSubscription], int]:
        total_result = await self.session.execute(
            select(func.count()).select_from(WebhookSubscription)
        )
        total = total_result.scalar_one()

        result = await self.session.execute(
            select(WebhookSubscription)
            .order_by(WebhookSubscription.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def update_subscription(
        self,
        subscription: WebhookSubscription,
        **kwargs,
    ) -> WebhookSubscription:
        for key, value in kwargs.items():
            setattr(subscription, key, value)

        await self.session.flush()
        await self.session.refresh(subscription)
        return subscription

    async def create_delivery(
        self,
        delivery: WebhookDelivery,
    ) -> WebhookDelivery:
        self.session.add(delivery)
        await self.session.flush()
        await self.session.refresh(delivery)
        return delivery

    async def get_delivery(self, delivery_id: int) -> WebhookDelivery | None:
        result = await self.session.execute(
            select(WebhookDelivery)
            .options(selectinload(WebhookDelivery.subscription))
            .where(WebhookDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def list_deliveries(
        self,
        subscription_id: int,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[WebhookDelivery], int]:
        total_result = await self.session.execute(
            select(func.count())
            .select_from(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
        )
        total = total_result.scalar_one()

        result = await self.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == subscription_id)
            .order_by(WebhookDelivery.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, total

    async def list_failed_deliveries(self, limit: int = 100) -> list[WebhookDelivery]:
        result = await self.session.execute(
            select(WebhookDelivery)
            .options(selectinload(WebhookDelivery.subscription))
            .where(WebhookDelivery.status == "failed")
            .order_by(WebhookDelivery.id.desc())
            .limit(limit)
        )
        return list(result.scalars().all())