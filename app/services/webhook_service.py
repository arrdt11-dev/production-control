from typing import Any

from fastapi import HTTPException, status

from app.models import WebhookDelivery, WebhookSubscription
from app.schemas.webhook import EventType, WebhookCreate, WebhookUpdate
from app.tasks.webhooks import send_webhook_delivery
from app.uow import UnitOfWork


class WebhookService:
    @staticmethod
    async def create_subscription(
        uow: UnitOfWork,
        data: WebhookCreate,
    ) -> WebhookSubscription:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

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
    async def create_webhook(
        uow: UnitOfWork,
        data: WebhookCreate,
    ) -> WebhookSubscription:
        return await WebhookService.create_subscription(uow, data)

    @staticmethod
    async def get_subscription(
        uow: UnitOfWork,
        webhook_id: int,
    ) -> WebhookSubscription:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        webhook = await uow.webhooks.get_subscription(webhook_id)
        if webhook is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with id={webhook_id} not found",
            )
        return webhook

    @staticmethod
    async def get_webhook(
        uow: UnitOfWork,
        webhook_id: int,
    ) -> WebhookSubscription:
        return await WebhookService.get_subscription(uow, webhook_id)

    @staticmethod
    async def list_subscriptions(
        uow: UnitOfWork,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[WebhookSubscription], int]:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        return await uow.webhooks.list_subscriptions(offset=offset, limit=limit)

    @staticmethod
    async def list_webhooks(
        uow: UnitOfWork,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[WebhookSubscription], int]:
        return await WebhookService.list_subscriptions(uow, offset=offset, limit=limit)

    @staticmethod
    async def update_subscription(
        uow: UnitOfWork,
        webhook_id: int,
        data: WebhookUpdate,
    ) -> WebhookSubscription:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        webhook = await uow.webhooks.get_subscription(webhook_id)
        if webhook is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with id={webhook_id} not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        if "url" in update_data and update_data["url"] is not None:
            update_data["url"] = str(update_data["url"])

        updated = await uow.webhooks.update_subscription(webhook, **update_data)
        await uow.commit()
        return updated

    @staticmethod
    async def update_webhook(
        uow: UnitOfWork,
        webhook_id: int,
        data: WebhookUpdate,
    ) -> WebhookSubscription:
        return await WebhookService.update_subscription(uow, webhook_id, data)

    @staticmethod
    async def delete_subscription(
        uow: UnitOfWork,
        webhook_id: int,
    ) -> None:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        webhook = await uow.webhooks.get_subscription(webhook_id)
        if webhook is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with id={webhook_id} not found",
            )

        await uow.webhooks.update_subscription(webhook, is_active=False)
        await uow.commit()

    @staticmethod
    async def delete_webhook(
        uow: UnitOfWork,
        webhook_id: int,
    ) -> None:
        await WebhookService.delete_subscription(uow, webhook_id)

    @staticmethod
    async def list_deliveries(
        uow: UnitOfWork,
        subscription_id: int,
        offset: int = 0,
        limit: int = 100,
    ) -> tuple[list[WebhookDelivery], int]:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        webhook = await uow.webhooks.get_subscription(subscription_id)
        if webhook is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Webhook with id={subscription_id} not found",
            )

        return await uow.webhooks.list_deliveries(
            subscription_id=subscription_id,
            offset=offset,
            limit=limit,
        )

    @staticmethod
    async def _collect_matching_subscriptions(
        uow: UnitOfWork,
        event_value: str,
        page_size: int = 200,
    ) -> list[WebhookSubscription]:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        matched: list[WebhookSubscription] = []
        offset = 0

        while True:
            subscriptions, total = await uow.webhooks.list_subscriptions(
                offset=offset,
                limit=page_size,
            )

            if not subscriptions:
                break

            for subscription in subscriptions:
                if not subscription.is_active:
                    continue

                subscription_events = subscription.events or []
                if event_value not in subscription_events:
                    continue

                matched.append(subscription)

            offset += len(subscriptions)
            if offset >= total:
                break

        return matched

    @staticmethod
    async def create_event_deliveries(
        uow: UnitOfWork,
        event_type: EventType | str,
        payload: dict[str, Any],
    ) -> list[WebhookDelivery]:
        if uow.webhooks is None:
            raise RuntimeError("UnitOfWork is not initialized: webhooks is None")

        event_value = (
            event_type.value if isinstance(event_type, EventType) else str(event_type)
        )

        subscriptions = await WebhookService._collect_matching_subscriptions(
            uow=uow,
            event_value=event_value,
        )

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