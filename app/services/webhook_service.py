from typing import Any

from fastapi import HTTPException, status

from app.models import WebhookDelivery, WebhookSubscription
from app.schemas.webhook import EventType, WebhookCreate, WebhookUpdate
from app.tasks.webhooks import send_webhook_delivery
from app.uow import UnitOfWork


class WebhookService:
    @staticmethod
    async def create_subscription(uow: UnitOfWork, data: WebhookCreate) -> WebhookSubscription:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized")

        subscription = WebhookSubscription(
            url=str(data.url),
            events=data.events,
            secret_key=data.secret_key,
            is_active=True,
            retry_count=data.retry_count,
            timeout=data.timeout,
        )

        created = await uow.webhooks.create_subscription(subscription)
        await uow.commit()
        return created

    @staticmethod
    async def get_subscription(uow: UnitOfWork, webhook_id: int) -> WebhookSubscription:
        webhook = await uow.webhooks.get_subscription(webhook_id)
        if webhook is None:
            raise HTTPException(status_code=404, detail="Webhook not found")
        return webhook

    @staticmethod
    async def list_subscriptions(uow: UnitOfWork, offset=0, limit=100):
        return await uow.webhooks.list_subscriptions(offset=offset, limit=limit)

    @staticmethod
    async def update_subscription(uow: UnitOfWork, webhook_id: int, data: WebhookUpdate):
        webhook = await uow.webhooks.get_subscription(webhook_id)
        if webhook is None:
            raise HTTPException(status_code=404, detail="Webhook not found")

        update_data = data.model_dump(exclude_unset=True)

        if "url" in update_data:
            update_data["url"] = str(update_data["url"])

        updated = await uow.webhooks.update_subscription(webhook, **update_data)
        await uow.commit()
        return updated

    @staticmethod
    async def delete_subscription(uow: UnitOfWork, webhook_id: int):
        webhook = await uow.webhooks.get_subscription(webhook_id)
        if webhook is None:
            raise HTTPException(status_code=404, detail="Webhook not found")

        await uow.webhooks.update_subscription(webhook, is_active=False)
        await uow.commit()

    @staticmethod
    async def list_deliveries(uow: UnitOfWork, subscription_id: int, offset=0, limit=100):
        webhook = await uow.webhooks.get_subscription(subscription_id)
        if webhook is None:
            raise HTTPException(status_code=404, detail="Webhook not found")

        return await uow.webhooks.list_deliveries(
            subscription_id=subscription_id,
            offset=offset,
            limit=limit,
        )

    @staticmethod
    async def create_event_deliveries(
        uow: UnitOfWork,
        event_type: EventType | str,
        payload: dict[str, Any],
    ) -> list[WebhookDelivery]:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized")

        event_value = event_type.value if isinstance(event_type, EventType) else str(event_type)


        subscriptions = await uow.webhooks.get_active_by_event(event_value)

        created_deliveries: list[WebhookDelivery] = []

        for subscription in subscriptions:
            delivery = WebhookDelivery(
                subscription_id=subscription.id,
                event_type=event_value,
                payload=payload,
                status="pending",
                attempts=0,
                response_status=None,
                response_body=None,
                error_message=None,
                delivered_at=None,
            )

            created = await uow.webhooks.create_delivery(delivery)
            created_deliveries.append(created)

        await uow.commit()

        for delivery in created_deliveries:
            send_webhook_delivery.delay(delivery.id)

        return created_deliveries