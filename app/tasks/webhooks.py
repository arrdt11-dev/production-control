import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.celery_app import celery_app
from app.models import WebhookDelivery, WebhookSubscription
from app.settings import settings

_sync_engine = None
_SyncSessionLocal = None


def get_sync_engine():
    global _sync_engine

    if _sync_engine is None:
        sync_database_url = settings.database_url.replace("+asyncpg", "")
        _sync_engine = create_engine(
            sync_database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=settings.db_pool_recycle,
            future=True,
        )

    return _sync_engine


def get_sync_session_local():
    global _SyncSessionLocal

    if _SyncSessionLocal is None:
        _SyncSessionLocal = sessionmaker(
            bind=get_sync_engine(),
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    return _SyncSessionLocal


def _build_signature(secret_key: str, payload: dict[str, Any]) -> str:
    if not secret_key or not secret_key.strip():
        raise ValueError("secret_key cannot be empty")

    body = json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    signature = hmac.new(
        secret_key.encode("utf-8"),
        body,
        hashlib.sha256,
    ).hexdigest()

    return f"sha256={signature}"


@celery_app.task(name="app.tasks.webhooks.send_webhook_delivery")
def send_webhook_delivery(delivery_id: int) -> dict[str, Any]:
    db = get_sync_session_local()()

    try:
        delivery = db.execute(
            select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
        ).scalar_one_or_none()

        if delivery is None:
            return {
                "success": False,
                "delivery_id": delivery_id,
                "error": f"WebhookDelivery with id={delivery_id} not found",
            }

        subscription = db.execute(
            select(WebhookSubscription).where(
                WebhookSubscription.id == delivery.subscription_id
            )
        ).scalar_one_or_none()

        if subscription is None:
            delivery.status = "failed"
            delivery.error_message = (
                f"WebhookSubscription with id={delivery.subscription_id} not found"
            )
            delivery.attempts += 1
            delivery.delivered_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "success": False,
                "delivery_id": delivery_id,
                "error": delivery.error_message,
            }

        if not subscription.is_active:
            delivery.status = "failed"
            delivery.error_message = "Webhook subscription is inactive"
            delivery.attempts += 1
            delivery.delivered_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "success": False,
                "delivery_id": delivery_id,
                "error": delivery.error_message,
            }

        try:
            signature = _build_signature(subscription.secret_key, delivery.payload)

            with httpx.Client(timeout=subscription.timeout) as client:
                response = client.post(
                    subscription.url,
                    json=delivery.payload,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Event": delivery.event_type,
                        "X-Webhook-Delivery-Id": str(delivery.id),
                        "X-Webhook-Signature": signature,
                    },
                )

            is_success = 200 <= response.status_code < 300

            delivery.status = "success" if is_success else "failed"
            delivery.response_status = response.status_code
            delivery.response_body = response.text
            delivery.error_message = None if is_success else response.text
            delivery.delivered_at = datetime.now(timezone.utc)
            delivery.attempts += 1

            db.commit()

            return {
                "success": is_success,
                "delivery_id": delivery_id,
                "status_code": response.status_code,
            }

        except Exception as exc:
            delivery.status = "failed"
            delivery.error_message = str(exc)
            delivery.attempts += 1
            delivery.delivered_at = datetime.now(timezone.utc)
            db.commit()

            return {
                "success": False,
                "delivery_id": delivery_id,
                "error": str(exc),
            }

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()