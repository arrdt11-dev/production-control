from __future__ import annotations

from app.models import Product
from app.schemas.product import ProductCreate
from app.uow import UnitOfWork


class ProductService:
    @staticmethod
    async def add_product(uow: UnitOfWork, data: ProductCreate) -> Product:
        assert uow.products
        product = Product(unique_code=data.unique_code, batch_id=data.batch_id)
        await uow.products.create(product)
        await uow.commit()
        assert uow.session
        await uow.session.refresh(product)
        return product

    @staticmethod
    async def aggregate_sync(uow: UnitOfWork, batch_id: int, codes: list[str]) -> dict:
        assert uow.products and uow.batches
        batch = await uow.batches.get_by_id(batch_id)
        if not batch:
            return {"success": False, "message": "Batch not found"}

        result = await uow.products.aggregate_codes_in_batch(batch_id, codes)
        await uow.commit()
        return result
