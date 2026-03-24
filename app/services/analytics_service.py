from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Batch, Product


class AnalyticsService:
    @staticmethod
    async def get_dashboard(session: AsyncSession) -> dict:
        total_batches = await session.scalar(select(func.count(Batch.id))) or 0
        active_batches = await session.scalar(
            select(func.count(Batch.id)).where(Batch.is_closed.is_(False))
        ) or 0
        closed_batches = await session.scalar(
            select(func.count(Batch.id)).where(Batch.is_closed.is_(True))
        ) or 0

        total_products = await session.scalar(select(func.count(Product.id))) or 0
        aggregated_products = await session.scalar(
            select(func.count(Product.id)).where(Product.is_aggregated.is_(True))
        ) or 0

        aggregation_rate = round(
            (aggregated_products / total_products * 100) if total_products else 0.0, 2
        )

        return {
            "summary": {
                "total_batches": total_batches,
                "active_batches": active_batches,
                "closed_batches": closed_batches,
                "total_products": total_products,
                "aggregated_products": aggregated_products,
                "aggregation_rate": aggregation_rate,
            }
        }

    @staticmethod
    async def get_batch_statistics(session: AsyncSession, batch_id: int) -> dict | None:
        batch = await session.get(Batch, batch_id)
        if not batch:
            return None

        total_products = await session.scalar(
            select(func.count(Product.id)).where(Product.batch_id == batch_id)
        ) or 0

        aggregated = await session.scalar(
            select(func.count(Product.id)).where(
                Product.batch_id == batch_id,
                Product.is_aggregated.is_(True),
            )
        ) or 0

        remaining = total_products - aggregated
        aggregation_rate = round(
            (aggregated / total_products * 100) if total_products else 0.0, 2
        )

        shift_start = batch.shift_start
        shift_end = batch.shift_end

        if shift_start.tzinfo is None:
            shift_start = shift_start.replace(tzinfo=timezone.utc)
        if shift_end.tzinfo is None:
            shift_end = shift_end.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)

        shift_duration_hours = max((shift_end - shift_start).total_seconds() / 3600, 0.0)
        elapsed_hours = max(
            min((now - shift_start).total_seconds() / 3600, shift_duration_hours), 0.0
        )

        products_per_hour = round(
            (aggregated / elapsed_hours) if elapsed_hours > 0 else 0.0, 2
        )

        estimated_completion = None
        if products_per_hour > 0 and remaining > 0:
            estimated_completion = (
                now + timedelta(hours=remaining / products_per_hour)
            ).isoformat()

        return {
            "batch_info": {
                "id": batch.id,
                "batch_number": batch.batch_number,
                "batch_date": str(batch.batch_date),
                "is_closed": batch.is_closed,
            },
            "production_stats": {
                "total_products": total_products,
                "aggregated": aggregated,
                "remaining": remaining,
                "aggregation_rate": aggregation_rate,
            },
            "timeline": {
                "shift_duration_hours": round(shift_duration_hours, 2),
                "elapsed_hours": round(elapsed_hours, 2),
                "products_per_hour": products_per_hour,
                "estimated_completion": estimated_completion,
            },
            "team_performance": {
                "team": batch.team,
                "avg_products_per_hour": products_per_hour,
                "efficiency_score": aggregation_rate,
            },
        }

    @staticmethod
    async def compare_batches(session: AsyncSession, batch_ids: list[int]) -> dict:
        if not batch_ids:
            return {
                "comparison": [],
                "average": {"aggregation_rate": 0.0, "products_per_hour": 0.0},
            }

        batches = (
            await session.execute(
                select(Batch).where(Batch.id.in_(batch_ids))
            )
        ).scalars().all()

        if not batches:
            return {
                "comparison": [],
                "average": {"aggregation_rate": 0.0, "products_per_hour": 0.0},
            }

        stats = (
            await session.execute(
                select(
                    Product.batch_id,
                    func.count(Product.id).label("total"),
                    func.count(Product.id)
                    .filter(Product.is_aggregated.is_(True))
                    .label("aggregated"),
                )
                .where(Product.batch_id.in_(batch_ids))
                .group_by(Product.batch_id)
            )
        ).all()

        stats_map = {
            row.batch_id: {"total": row.total, "aggregated": row.aggregated}
            for row in stats
        }

        comparison = []

        for batch in batches:
            stat = stats_map.get(batch.id, {"total": 0, "aggregated": 0})

            total_products = stat["total"]
            aggregated = stat["aggregated"]

            rate = round(
                (aggregated / total_products * 100) if total_products else 0.0, 2
            )

            duration_hours = max(
                (batch.shift_end - batch.shift_start).total_seconds() / 3600,
                0.0,
            )

            products_per_hour = round(
                (aggregated / duration_hours) if duration_hours > 0 else 0.0,
                2,
            )

            comparison.append(
                {
                    "batch_id": batch.id,
                    "batch_number": batch.batch_number,
                    "total_products": total_products,
                    "aggregated": aggregated,
                    "rate": rate,
                    "duration_hours": round(duration_hours, 2),
                    "products_per_hour": products_per_hour,
                }
            )

        avg_rate = (
            round(sum(x["rate"] for x in comparison) / len(comparison), 2)
            if comparison
            else 0.0
        )

        avg_pph = (
            round(
                sum(x["products_per_hour"] for x in comparison) / len(comparison), 2
            )
            if comparison
            else 0.0
        )

        return {
            "comparison": comparison,
            "average": {
                "aggregation_rate": avg_rate,
                "products_per_hour": avg_pph,
            },
        }