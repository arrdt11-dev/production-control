from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Batch, Product


class AnalyticsService:
    @staticmethod
    async def get_dashboard(session: AsyncSession) -> dict:
        stmt = select(
            func.count(Batch.id).label("total_batches"),
            func.coalesce(
                func.sum(case((Batch.is_closed.is_(False), 1), else_=0)),
                0,
            ).label("active_batches"),
            func.coalesce(
                func.sum(case((Batch.is_closed.is_(True), 1), else_=0)),
                0,
            ).label("closed_batches"),
        )
        batch_row = (await session.execute(stmt)).one()

        product_stmt = select(
            func.count(Product.id).label("total_products"),
            func.coalesce(
                func.sum(case((Product.is_aggregated.is_(True), 1), else_=0)),
                0,
            ).label("aggregated_products"),
        )
        product_row = (await session.execute(product_stmt)).one()

        total_batches = int(batch_row.total_batches or 0)
        active_batches = int(batch_row.active_batches or 0)
        closed_batches = int(batch_row.closed_batches or 0)
        total_products = int(product_row.total_products or 0)
        aggregated_products = int(product_row.aggregated_products or 0)

        aggregation_rate = (
            round((aggregated_products / total_products) * 100, 2)
            if total_products > 0
            else 0.0
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
    async def get_batch_statistics(session: AsyncSession, batch_id: int) -> dict:
        batch = await session.get(Batch, batch_id)
        if batch is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        stats_stmt = select(
            func.count(Product.id).label("total_products"),
            func.coalesce(
                func.sum(case((Product.is_aggregated.is_(True), 1), else_=0)),
                0,
            ).label("aggregated"),
        ).where(Product.batch_id == batch_id)

        stats_row = (await session.execute(stats_stmt)).one()

        total_products = int(stats_row.total_products or 0)
        aggregated = int(stats_row.aggregated or 0)
        remaining = total_products - aggregated
        aggregation_rate = (
            round((aggregated / total_products) * 100, 2)
            if total_products > 0
            else 0.0
        )

        shift_duration_hours = 0.0
        elapsed_hours = 0.0
        products_per_hour = 0.0

        if batch.shift_start and batch.shift_end:
            start_dt = (
                batch.shift_start.replace(tzinfo=timezone.utc)
                if batch.shift_start.tzinfo is None
                else batch.shift_start
            )
            end_dt = (
                batch.shift_end.replace(tzinfo=timezone.utc)
                if batch.shift_end.tzinfo is None
                else batch.shift_end
            )

            shift_duration_hours = round(
                (end_dt - start_dt).total_seconds() / 3600,
                2,
            )

            now = datetime.now(timezone.utc)

            if now > start_dt:
                elapsed_hours = round(
                    min((now - start_dt).total_seconds() / 3600, shift_duration_hours),
                    2,
                )

            if elapsed_hours > 0:
                products_per_hour = round(aggregated / elapsed_hours, 2)

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
                "shift_duration_hours": shift_duration_hours,
                "elapsed_hours": elapsed_hours,
                "products_per_hour": products_per_hour,
                "estimated_completion": None,
            },
            "team_performance": {
                "team": getattr(batch, "team", "") or "",
                "avg_products_per_hour": products_per_hour,
                "efficiency_score": aggregation_rate,
            },
        }

    @staticmethod
    async def compare_batches(session: AsyncSession, batch_ids: list[int]) -> dict:
        if not batch_ids:
            return {
                "comparison": [],
                "average": {
                    "aggregation_rate": 0.0,
                    "products_per_hour": 0.0,
                },
            }

        stmt = (
            select(
                Batch.id.label("batch_id"),
                Batch.batch_number,
                Batch.shift_start,
                Batch.shift_end,
                func.count(Product.id).label("total_products"),
                func.coalesce(
                    func.sum(
                        case(
                            (Product.is_aggregated.is_(True), 1),
                            else_=0,
                        )
                    ),
                    0,
                ).label("aggregated"),
            )
            .outerjoin(Product, Product.batch_id == Batch.id)
            .where(Batch.id.in_(batch_ids))
            .group_by(Batch.id, Batch.batch_number, Batch.shift_start, Batch.shift_end)
        )

        rows = (await session.execute(stmt)).all()

        if not rows:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No batches found for provided ids",
            )

        comparison: list[dict] = []

        for row in rows:
            duration_hours = 0.0
            if row.shift_start and row.shift_end:
                start_dt = (
                    row.shift_start.replace(tzinfo=timezone.utc)
                    if row.shift_start.tzinfo is None
                    else row.shift_start
                )
                end_dt = (
                    row.shift_end.replace(tzinfo=timezone.utc)
                    if row.shift_end.tzinfo is None
                    else row.shift_end
                )
                duration_hours = round(
                    (end_dt - start_dt).total_seconds() / 3600,
                    2,
                )

            total_products = int(row.total_products or 0)
            aggregated = int(row.aggregated or 0)

            rate = (
                round((aggregated / total_products) * 100, 2)
                if total_products > 0
                else 0.0
            )

            products_per_hour = (
                round(aggregated / duration_hours, 2)
                if duration_hours > 0
                else 0.0
            )

            comparison.append(
                {
                    "batch_id": row.batch_id,
                    "batch_number": row.batch_number,
                    "total_products": total_products,
                    "aggregated": aggregated,
                    "rate": rate,
                    "duration_hours": duration_hours,
                    "products_per_hour": products_per_hour,
                }
            )

        average_aggregation_rate = round(
            sum(item["rate"] for item in comparison) / len(comparison),
            2,
        )
        average_products_per_hour = round(
            sum(item["products_per_hour"] for item in comparison) / len(comparison),
            2,
        )

        return {
            "comparison": comparison,
            "average": {
                "aggregation_rate": average_aggregation_rate,
                "products_per_hour": average_products_per_hour,
            },
        }