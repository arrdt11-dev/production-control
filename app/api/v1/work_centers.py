from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.work_center import WorkCenterCreate, WorkCenterRead
from app.services.work_center_service import WorkCenterService
from app.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/work-centers", tags=["WorkCenters"])


@router.post("", response_model=WorkCenterRead, status_code=201)
async def create_work_center(data: WorkCenterCreate):
    async with UnitOfWork() as uow:
        created = await WorkCenterService.create(uow, data)
        await uow.commit()
        return created


@router.get("/{work_center_id}", response_model=WorkCenterRead)
async def get_work_center(work_center_id: int):
    async with UnitOfWork() as uow:
        wc = await WorkCenterService.get(uow, work_center_id)
        if not wc:
            raise HTTPException(status_code=404, detail="Work center not found")
        return wc


@router.get("", response_model=list[WorkCenterRead])
async def list_work_centers():
    async with UnitOfWork() as uow:
        return await WorkCenterService.list(uow)
