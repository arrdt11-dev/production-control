from app.schemas.webhook import WebhookCreate, WebhookUpdate


class WebhookService:
    @staticmethod
    async def create_subscription(uow, data: WebhookCreate):
        obj = await uow.webhooks.create_subscription(
            url=data.url,
            events=data.events,
            secret_key=data.secret_key,
            is_active=True,
            retry_count=data.retry_count,
            timeout=data.timeout,
        )
        return obj

    @staticmethod
    async def list_subscriptions(uow, offset: int = 0, limit: int = 100):
        return await uow.webhooks.list_subscriptions(offset=offset, limit=limit)

    @staticmethod
    async def update_subscription(uow, webhook_id: int, data: WebhookUpdate):
        payload = data.model_dump(exclude_none=True)
        return await uow.webhooks.update_subscription(webhook_id, **payload)

    @staticmethod
    async def delete_subscription(uow, webhook_id: int):
        return await uow.webhooks.delete_subscription(webhook_id)

    @staticmethod
    async def list_deliveries(uow, webhook_id: int, offset: int = 0, limit: int = 100):
        return await uow.webhooks.list_deliveries(webhook_id, offset=offset, limit=limit)

    @staticmethod
    async def create_event