from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select

from app.models import Product
from app.schemas.webhook import EventType
from app.services.webhook_service import WebhookService
from app.uow import UnitOfWork


class ReportService:
    @staticmethod
    async def generate_batch_report(
        uow: UnitOfWork,
        batch_id: int,
    ) -> dict:
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches is None")

        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        batch = await uow.batches.get(batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        result = await uow.session.execute(
            select(Product).where(Product.batch_id == batch_id)
        )
        products = result.scalars().all()

        total_products = len(products)
        aggregated_products = sum(1 for product in products if product.is_aggregated)
        remaining_products = total_products - aggregated_products
        aggregation_rate = (
            round((aggregated_products / total_products) * 100, 2)
            if total_products > 0
            else 0.0
        )

        report_data = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "batch": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "work_center_id": batch.work_center_id,
                "batch_date": str(batch.batch_date),
                "shift_start": batch.shift_start.isoformat() if batch.shift_start else None,
                "shift_end": batch.shift_end.isoformat() if batch.shift_end else None,
                "task_description": batch.task_description,
                "shift": getattr(batch, "shift", "") or "",
                "team": getattr(batch, "team", "") or "",
                "nomenclature": getattr(batch, "nomenclature", "") or "",
                "ekn_code": getattr(batch, "ekn_code", "") or "",
                "is_closed": batch.is_closed,
            },
            "summary": {
                "total_products": total_products,
                "aggregated_products": aggregated_products,
                "remaining_products": remaining_products,
                "aggregation_rate": aggregation_rate,
            },
            "products": [
                {
                    "id": product.id,
                    "unique_code": product.unique_code,
                    "is_aggregated": product.is_aggregated,
                    "aggregated_at": (
                        product.aggregated_at.isoformat()
                        if product.aggregated_at
                        else None
                    ),
                }
                for product in products
            ],
        }

        await WebhookService.create_event_deliveries(
            uow=uow,
            event_type=EventType.REPORT_GENERATED,
            payload={
                "batch_id": batch.id,
                "batch_number": batch.batch_number,
                "generated_at": report_data["generated_at"],
                "summary": report_data["summary"],
            },
        )

        return {
            "success": True,
            "batch_id": batch_id,
            "report": report_data,
        }