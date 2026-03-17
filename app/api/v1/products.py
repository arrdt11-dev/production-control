from fastapi import APIRouter, HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.schemas.product import ProductCreate, ProductRead
from app.services.product_service import ProductService
from app.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post("", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def add_product(data: ProductCreate):
    async with UnitOfWork() as uow:
        try:
            return await ProductService.add_product(uow, data)
        except IntegrityError as e:
            await uow.session.rollback()

            error_text = str(e.orig).lower() if getattr(e, "orig", None) else str(e).lower()

            if "ix_products_unique_code" in error_text or "unique_code" in error_text:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with unique_code='{data.unique_code}' already exists"
                )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create product due to database constraint"
            )