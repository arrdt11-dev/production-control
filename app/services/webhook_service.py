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
    async def create_event_deliveries(uow, event_type: str, payload: dict):
        subs, _ = await uow.webhooks.list_subscriptions(offset=0, limit=1000)
        created = []

        for sub in subs:
            if not sub.is_active:
                continue
            if event_type not in sub.events:
                continue

            delivery = await uow.webhooks.create_delivery(
                subscription_id=sub.id,
                event_type=event_type,
                payload=payload,
                status="pending",
                attempts=0,
            )
            created.append(delivery)

        return created

    @staticmethod
    def build_batch_created_payload(batch) -> dict:
        return {
            "event": "batch_created",
            "data": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "batch_date": str(batch.batch_date),
                "nomenclature": batch.nomenclature,
                "work_center_id": batch.work_center_id,
            },
            "timestamp": batch.created_at.isoformat() if batch.created_at else None,
        }

    @staticmethod
    def build_batch_closed_payload(batch, statistics: dict | None = None) -> dict:
        return {
            "event": "batch_closed",
            "data": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "closed_at": batch.closed_at.isoformat() if batch.closed_at else None,
                "statistics": statistics or {},
            },
            "timestamp": batch.closed_at.isoformat() if batch.closed_at else None,
        }

    @staticmethod
    def build_report_generated_payload(batch_id: int, report_type: str, file_url: str, expires_at: str | None) -> dict:
        return {
            "event": "report_generated",
            "data": {
                "batch_id": batch_id,
                "report_type": report_type,
                "file_url": file_url,
                "expires_at": expires_at,
            },
            "timestamp": expires_at,
        }
