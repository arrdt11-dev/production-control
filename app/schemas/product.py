from datetime import datetime
from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    unique_code: str = Field(min_length=1, max_length=64)
    batch_id: int


class ProductRead(BaseModel):
    id: int
    unique_code: str
    is_aggregated: bool
    aggregated_at: datetime | None

    model_config = {"from_attributes": True}
