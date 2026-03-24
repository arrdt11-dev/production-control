from fastapi import HTTPException, status


class ProductService:
    @staticmethod
    async def aggregate_sync(uow, batch_id: int, unique_codes: list[str]) -> dict:
        if uow.products is None or uow.batches is None:
            raise RuntimeError("UnitOfWork repositories are not initialized")

        batch = await uow.batches.get(batch_id)
        if not batch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Batch with id={batch_id} not found",
            )

        result = await uow.products.aggregate_codes_in_batch(batch_id, unique_codes)

        await uow.commit()
        return result