from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.models import WebhookDelivery, WebhookSubscription


class WebhookRepository:
    def __init__(self, session):
        self.session = session

    async def create_subscription(self, **kwargs) -> WebhookSubscription:
        obj = WebhookSubscription(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def list_subscriptions(self, offset: int = 0, limit: int = 100):
        total = await self.session.scalar(
            select(func.count()).select_from(WebhookSubscription)
        )
        result = await self.session.execute(
            select(WebhookSubscription)
            .order_by(WebhookSubscription.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, int(total or 0)

    async def get_subscription(self, webhook_id: int) -> WebhookSubscription | None:
        result = await self.session.execute(
            select(WebhookSubscription).where(WebhookSubscription.id == webhook_id)
        )
        return result.scalar_one_or_none()

    async def update_subscription(self, webhook_id: int, **kwargs) -> WebhookSubscription | None:
        obj = await self.get_subscription(webhook_id)
        if not obj:
            return None

        for key, value in kwargs.items():
            setattr(obj, key, value)

        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete_subscription(self, webhook_id: int) -> bool:
        obj = await self.get_subscription(webhook_id)
        if not obj:
            return False
        await self.session.delete(obj)
        await self.session.flush()
        return True

    async def create_delivery(
        self,
        subscription_id: int,
        event_type: str,
        payload: dict,
        status: str = "pending",
        attempts: int = 0,
    ) -> WebhookDelivery:
        obj = WebhookDelivery(
            subscription_id=subscription_id,
            event_type=event_type,
            payload=payload,
            status=status,
            attempts=attempts,
        )
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get_delivery(self, delivery_id: int) -> WebhookDelivery | None:
        result = await self.session.execute(
            select(WebhookDelivery)
            .options(selectinload(WebhookDelivery.subscription))
            .where(WebhookDelivery.id == delivery_id)
        )
        return result.scalar_one_or_none()

    async def list_deliveries(self, webhook_id: int, offset: int = 0, limit: int = 100):
        total = await self.session.scalar(
            select(func.count()).select_from(WebhookDelivery).where(
                WebhookDelivery.subscription_id == webhook_id
            )
        )
        result = await self.session.execute(
            select(WebhookDelivery)
            .where(WebhookDelivery.subscription_id == webhook_id)
            .order_by(WebhookDelivery.id.desc())
            .offset(offset)
            .limit(limit)
        )
        items = list(result.scalars().all())
        return items, int(total or 0)

    async def list_failed_deliveries(self, limit: int = 100):
        result = await self.session.execute(
            select(WebhookDelivery)
            .options(selectinload(WebhookDelivery.subscription))
            .where(WebhookDelivery.status == "failed")
            .order_by(WebhookDelivery.id.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
