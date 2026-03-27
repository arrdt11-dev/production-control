from fastapi import APIRouter, HTTPException, Query, Response

from app.schemas.webhook import (
    WebhookCreate,
    WebhookDeliveryListResponse,
    WebhookListResponse,
    WebhookRead,
    WebhookUpdate,
)
from app.services.webhook_service import WebhookService
from app.tasks.webhooks import send_webhook_delivery
from app.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])


@router.post("/", response_model=WebhookRead, status_code=201)
async def create_webhook(body: WebhookCreate):
    async with UnitOfWork() as uow:
        obj = await WebhookService.create_subscription(uow, body)
        await uow.commit()
        return obj


@router.get("/", response_model=WebhookListResponse)
async def list_webhooks(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    async with UnitOfWork() as uow:
        items, total = await WebhookService.list_subscriptions(uow, offset=offset, limit=limit)
        return {"items": items, "total": total}


@router.patch("/{webhook_id}", response_model=WebhookRead)
async def update_webhook(webhook_id: int, body: WebhookUpdate):
    async with UnitOfWork() as uow:
        obj = await WebhookService.update_subscription(uow, webhook_id, body)
        if not obj:
            raise HTTPException(status_code=404, detail="Webhook subscription not found")
        await uow.commit()
        return obj


@router.delete("/{webhook_id}", status_code=204)
async def delete_webhook(webhook_id: int):
    async with UnitOfWork() as uow:
        deleted = await WebhookService.delete_subscription(uow, webhook_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Webhook subscription not found")
        await uow.commit()
        return Response(status_code=204)


@router.get("/{webhook_id}/deliveries", response_model=WebhookDeliveryListResponse)
async def list_webhook_deliveries(
    webhook_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
):
    async with UnitOfWork() as uow:
        items, total = await WebhookService.list_deliveries(
            uow, webhook_id, offset=offset, limit=limit
        )
        return {"items": items, "total": total}


@router.post("/deliveries/{delivery_id}/retry")
async def retry_webhook_delivery(delivery_id: int):
    task = send_webhook_delivery.delay(delivery_id)
    return {
        "status": "queued",
        "delivery_id": delivery_id,
        "task_id": task.id,
    }