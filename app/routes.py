from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import WorkCenter
from app.schemas import WorkCenterCreate, WorkCenterRead

router = APIRouter(prefix="/api/v1", tags=["WorkCenters"])


@router.post("/work-centers", response_model=WorkCenterRead, status_code=201)
async def create_work_center(
    data: WorkCenterCreate,
    db: AsyncSession = Depends(get_db),
):
    existing = await db.scalar(
        select(WorkCenter).where(WorkCenter.identifier == data.identifier)
    )
    if existing:
        raise HTTPException(status_code=409, detail="WorkCenter identifier already exists")

    wc = WorkCenter(identifier=data.identifier, name=data.name)
    db.add(wc)
    await db.commit()
    await db.refresh(wc)
    return wc


@router.get("/work-centers/{work_center_id}", response_model=WorkCenterRead)
async def get_work_center(
    work_center_id: int,
    db: AsyncSession = Depends(get_db),
):
    wc = await db.get(WorkCenter, work_center_id)
    if not wc:
        raise HTTPException(status_code=404, detail="WorkCenter not found")
    return wc


@router.get("/work-centers", response_model=list[WorkCenterRead])
async def list_work_centers(
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(WorkCenter).order_by(WorkCenter.id))
    return list(result.scalars().all())
