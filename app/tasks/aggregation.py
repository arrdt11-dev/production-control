import asyncio

from app.celery_app import celery_app
from app.services.product_service import ProductService
from app.uow import UnitOfWork


async def _run_aggregate(batch_id: int, unique_codes: list[str]) -> dict:
    async with UnitOfWork() as uow:
        return await ProductService.aggregate_sync(uow, batch_id, unique_codes)


@celery_app.task(
    bind=True,
    max_retries=3,
    name="app.tasks.aggregation.aggregate_products_batch",
)
def aggregate_products_batch(
    self,
    batch_id: int,
    unique_codes: list[str],
    user_id: int | None = None,
) -> dict:
    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(_run_aggregate(batch_id, unique_codes))
        return result
    finally:
        try:
            loop.close()
        except Exception:
            pass