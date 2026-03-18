from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.analytics import (
    DashboardResponse,
    CompareBatchesRequest,
    CompareBatchesResponse,
)
from app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["Analytics"])


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(session: AsyncSession = Depends(get_db)):
    return await AnalyticsService.get_dashboard(session)


@router.post("/compare-batches", response_model=CompareBatchesResponse)
async def compare_batches(
    body: CompareBatchesRequest,
    session: AsyncSession = Depends(get_db),
):
    return await AnalyticsService.compare_batches(session, body.batch_ids)
