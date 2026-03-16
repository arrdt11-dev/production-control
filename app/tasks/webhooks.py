import asyncio
import hashlib
import hmac
import json
from datetime import UTC, datetime

import httpx
from celery import shared_task

from app.database import async_session
from app.repositories.webhook import WebhookRepository


def _build_signature(secret_key: str, payload: dict) -> str:
    body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(
        secret_key.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()
    return signature


async def _send_webhook_delivery_async(delivery_id: int):
    async with async_session() as session:
        repo = WebhookRepository(session)
        delivery = await repo.get_delivery(delivery_id)

        if not delivery:
            return {"success": False, "error": f"Delivery with id={delivery_id} not found"}

        subscription = delivery.subscription
        if not subscription or not subscription.is_active:
            delivery.status = "failed"
            delivery.error_message = "Subscription inactive or missing"
            delivery.attempts += 1
            await session.commit()
            return {"success": False, "error": delivery.error_message}

        signature = _build_signature(subscription.secret_key, delivery.payload)

        headers = {
            "Content-Type": "application/json",
            "X-Webhook-Event": delivery.event_type,
            "X-Webhook-Signature": signature,
        }

        try:
            async with httpx.AsyncClient(timeout=subscription.timeout) as client:
                response = await client.post(
                    subscription.url,
                    json=delivery.payload,
                    headers=headers,
                )

            delivery.attempts += 1
            delivery.response_status = response.status_code
            delivery.response_body = response.text[:2000]

            if 200 <= response.status_code < 300:
                delivery.status = "success"
                delivery.error_message = None
                delivery.delivered_at = datetime.now(UTC)
            else:
                delivery.status = "failed"
                delivery.error_message = f"HTTP {response.status_code}"

            await session.commit()

            return {
                "success": delivery.status == "success",
                "delivery_id": delivery.id,
                "status": delivery.status,
                "response_status": delivery.response_status,
            }

        except Exception as e:
            delivery.attempts += 1
            delivery.status = "failed"
            delivery.error_message = str(e)
            await session.commit()
            return {
                "success": False,
                "delivery_id": delivery.id,
                "status": "failed",
                "error": str(e),
            }


@shared_task(bind=True, max_retries=3)
def send_webhook_delivery(self, delivery_id: int):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_send_webhook_delivery_async(delivery_id))
    finally:
        loop.close()
