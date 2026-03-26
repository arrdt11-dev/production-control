from fastapi import HTTPException, status

from app.models import WorkCenter
from app.schemas.work_center import WorkCenterCreate, WorkCenterUpdate
from app.uow import UnitOfWork


class WorkCenterService:
    @staticmethod
    async def create(uow: UnitOfWork, data: WorkCenterCreate) -> WorkCenter:
        if uow.work_centers is None:
            raise RuntimeError("UnitOfWork is not initialized: work_centers is None")

        work_center = WorkCenter(
            identifier=data.identifier,
            name=data.name,
        )

        created = await uow.work_centers.create(work_center)
        await uow.commit()
        return created

    @staticmethod
    async def list(uow: UnitOfWork) -> list[WorkCenter]:
        if uow.work_centers is None:
            raise RuntimeError("UnitOfWork is not initialized: work_centers is None")

        return await uow.work_centers.list()

    @staticmethod
    async def get(uow: UnitOfWork, work_center_id: int) -> WorkCenter:
        if uow.work_centers is None:
            raise RuntimeError("UnitOfWork is not initialized: work_centers is None")

        work_center = await uow.work_centers.get(work_center_id)
        if work_center is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work center with id={work_center_id} not found",
            )
        return work_center

    @staticmethod
    async def update(
        uow: UnitOfWork,
        work_center_id: int,
        data: WorkCenterUpdate,
    ) -> WorkCenter:
        if uow.work_centers is None:
            raise RuntimeError("UnitOfWork is not initialized: work_centers is None")

        work_center = await uow.work_centers.get(work_center_id)
        if work_center is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work center with id={work_center_id} not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        updated = await uow.work_centers.update(work_center, **update_data)
        await uow.commit()
        return updated