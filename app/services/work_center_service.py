from __future__ import annotations

from app.models import WorkCenter
from app.schemas.work_center import WorkCenterCreate, WorkCenterRead
from app.uow import UnitOfWork


class WorkCenterService:
    @staticmethod
    async def create(uow: UnitOfWork, data: WorkCenterCreate) -> WorkCenterRead:
        assert uow.work_centers is not None

        wc = WorkCenter(identifier=data.identifier, name=data.name)
        await uow.work_centers.add(wc)
        await uow.work_centers.flush()
        return WorkCenterRead.model_validate(wc)

    @staticmethod
    async def get(uow: UnitOfWork, work_center_id: int) -> WorkCenterRead | None:
        assert uow.work_centers is not None

        wc = await uow.work_centers.get(work_center_id)
        if not wc:
            return None
        return WorkCenterRead.model_validate(wc)

    @staticmethod
    async def list(uow: UnitOfWork) -> list[WorkCenterRead]:
        assert uow.work_centers is not None

        items = await uow.work_centers.list()
        return [WorkCenterRead.model_validate(x) for x in items]
