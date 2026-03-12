from __future__ import annotations

import asyncio

from app.celery_app import celery_app
from app.services.product_service import ProductService
from app.uow import UnitOfWork


async def _run_aggregate(batch_id: int, unique_codes: list[str]) -> dict:
    async with UnitOfWork() as uow:
        result = await ProductService.aggregate_sync(uow, batch_id, unique_codes)
        return result


@celery_app.task(bind=True, max_retries=3)
def aggregate_products_batch(self, batch_id: int, unique_codes: list[str], user_id: int | None = None):
    """
    Асинхронная массовая агрегация продукции.
    Реальная реализация через БД.
    """
    total = len(unique_codes)

    self.update_state(
        state="PROGRESS",
        meta={"current": 0, "total": total, "progress": 0},
    )

    try:
        result = asyncio.run(_run_aggregate(batch_id, unique_codes))
    except Exception as e:
        self.update_state(
            state="FAILURE",
            meta={
                "success": False,
                "error": str(e),
                "current": 0,
                "total": total,
                "progress": 0,
            },
        )
        raise

    self.update_state(
        state="PROGRESS",
        meta={"current": total, "total": total, "progress": 100},
    )

    return result