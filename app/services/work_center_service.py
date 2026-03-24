from fastapi import HTTPException, status


class WorkCenterService:
    @staticmethod
    async def get_by_id(uow, work_center_id: int):
        if uow.work_centers is None:
            raise RuntimeError("UnitOfWork.work_centers is not initialized")

        work_center = await uow.work_centers.get(work_center_id)
        if not work_center:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Work center with id={work_center_id} not found",
            )

        return work_center