from __future__ import annotations

from fastapi import APIRouter

from app.schemas import ProductCreate, ProductRead
from app.services.product_service import ProductService
from app.uow import UnitOfWork

router = APIRouter(prefix="/api/v1/products", tags=["Products"])


@router.post("", response_model=ProductRead, status_code=201)
async def add_product(data: ProductCreate):
    async with UnitOfWork() as uow:
        return await ProductService.add_product(uow, data)
