from pydantic import BaseModel, Field


class WorkCenterBase(BaseModel):
    identifier: str = Field(min_length=1, max_length=50)
    name: str = Field(min_length=1, max_length=255)


class WorkCenterCreate(WorkCenterBase):
    pass


class WorkCenterUpdate(BaseModel):
    identifier: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=255)


class WorkCenterRead(WorkCenterBase):
    id: int

    model_config = {"from_attributes": True}
