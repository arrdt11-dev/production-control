from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_unique_code(self, code: str) -> Product | None:
        return await self.session.scalar(select(Product).where(Product.unique_code == code))

    async def create(self, product: Product) -> Product:
        self.session.add(product)
        return product

    async def aggregate_codes_in_batch(self, batch_id: int, codes: list[str]) -> dict:
        """
        Синхронная агрегация: помечает продукты в партии aggregated=true, aggregated_at=now()
        Возвращает статистику как в ТЗ (упрощенно, без Celery прогресса).
        """
        now = datetime.now(timezone.utc)
        result = {"success": True, "total": len(codes), "aggregated": 0, "failed": 0, "errors": []}

        # Подтянем продукты
        res = await self.session.execute(
            select(Product).where(Product.batch_id == batch_id, Product.unique_code.in_(codes))
        )
        found = {p.unique_code: p for p in res.scalars().all()}

        for code in codes:
            p = found.get(code)
            if not p:
                result["failed"] += 1
                result["errors"].append({"code": code, "reason": "not found in batch"})
                continue
            if p.is_aggregated:
                result["failed"] += 1
                result["errors"].append({"code": code, "reason": "already aggregated"})
                continue

            p.is_aggregated = True
            p.aggregated_at = now
            result["aggregated"] += 1

        return result
