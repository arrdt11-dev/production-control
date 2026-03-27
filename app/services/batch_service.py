from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.models import Batch


class BatchService:
    @staticmethod
    async def create_batches(uow, items):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches repository is None")
        if uow.session is None:
            raise RuntimeError("UnitOfWork is not initialized: session is None")

        created_batches = []

        try:
            for item in items:
                batch = Batch(
                    batch_number=item.batch_number,
                    work_center_id=item.work_center_id,
                    shift_start=item.shift_start,
                    shift_end=item.shift_end,
                    task_description=getattr(item, "task_description", "") or "",
                    shift=getattr(item, "shift", "") or "",
                    team=getattr(item, "team", "") or "",
                    batch_date=(getattr(item, "batch_date", None) or item.shift_start.date()),
                    nomenclature=getattr(item, "nomenclature", "") or "",
                    ekn_code=getattr(item, "ekn_code", "") or "",
                    is_closed=False,
                )

                await uow.batches.create(batch)
                created_batches.append(batch)

            await uow.commit()
            return created_batches

        except IntegrityError as exc:
            await uow.session.rollback()
            raise HTTPException(
                status_code=409,
                detail="Batch with this number and date already exists",
            ) from exc

        except Exception:
            await uow.session.rollback()
            raise

    @staticmethod
    async def get_batches(uow, offset: int = 0, limit: int = 100):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches repository is None")
        return await uow.batches.list(offset=offset, limit=limit)

    @staticmethod
    async def get_batch(uow, batch_id: int):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches repository is None")

        batch = await uow.batches.get(batch_id)
        if batch is None:
            raise HTTPException(status_code=404, detail=f"Batch with id={batch_id} not found")
        return batch

    @staticmethod
    async def close_batch(uow, batch_id: int):
        if uow.batches is None:
            raise RuntimeError("UnitOfWork is not initialized: batches repository is None")

        batch = await uow.batches.get(batch_id)
        if batch is None:
            raise HTTPException(status_code=404, detail=f"Batch with id={batch_id} not found")

        batch.is_closed = True
        await uow.commit()
        return batch