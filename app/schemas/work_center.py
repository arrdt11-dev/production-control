from pydantic import BaseModel, Field


class WorkCenterRead(BaseModel):
    id: int
    identifier: str
    name: str

    model_config = {"from_attributes": True}


class WorkCenterRef(BaseModel):
    identifier: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)
