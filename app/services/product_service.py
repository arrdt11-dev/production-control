from datetime import datetime, timezone

from fastapi import HTTPException, status

from app.models import Product
from app.schemas.product import ProductCreate
from app.uow import UnitOfWork


class ProductService:
    @staticmethod
    async def add_product(uow: UnitOfWork, data: ProductCreate) -> Product:
        if uow.products is None:
            raise RuntimeError("UnitOfWork is not initialized: products is None")
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches is None")

        batch = await uow.batches.get(data.batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={data.batch_id} not found",
            )

        product = Product(
            unique_code=data.unique_code,
            batch_id=data.batch_id,
            is_aggregated=False,
            aggregated_at=None,
        )

        created = await uow.products.create(product)
        await uow.commit()
        return created

    @staticmethod
    async def aggregate_sync(
        uow: UnitOfWork,
        batch_id: int,
        unique_codes: list[str],
    ) -> dict:
        if uow.products is None:
            raise RuntimeError("UnitOfWork is not initialized: products is None")
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches is None")

        batch = await uow.batches.get(batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        aggregated = 0
        failed = 0
        errors: list[dict] = []

        for code in unique_codes:
            product = await uow.products.get_by_unique_code_in_batch(batch_id, code)

            if product is None:
                failed += 1
                errors.append(
                    {
                        "code": code,
                        "reason": "not found in batch",
                    }
                )
                continue

            if product.is_aggregated:
                failed += 1
                errors.append(
                    {
                        "code": code,
                        "reason": "already aggregated",
                    }
                )
                continue

            await uow.products.update(
                product,
                is_aggregated=True,
                aggregated_at=datetime.now(timezone.utc),
            )
            aggregated += 1

        await uow.commit()

        return {
            "success": True,
            "total": len(unique_codes),
            "aggregated": aggregated,
            "failed": failed,
            "errors": errors,
        }