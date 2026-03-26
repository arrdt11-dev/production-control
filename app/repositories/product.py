from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def get(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_by_unique_code_in_batch(
        self,
        batch_id: int,
        unique_code: str,
    ) -> Product | None:
        result = await self.session.execute(
            select(Product).where(
                Product.batch_id == batch_id,
                Product.unique_code == unique_code,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_batch(self, batch_id: int) -> list[Product]:
        result = await self.session.execute(
            select(Product)
            .where(Product.batch_id == batch_id)
            .order_by(Product.id)
        )
        return list(result.scalars().all())

    async def update(self, product: Product, **kwargs) -> Product:
        for key, value in kwargs.items():
            setattr(product, key, value)

        await self.session.flush()
        await self.session.refresh(product)
        return product