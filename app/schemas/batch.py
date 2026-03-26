from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class BatchFilters(BaseModel):
    is_closed: bool | None = None
    batch_number: int | None = None
    batch_date: date | None = None
    work_center_id: int | None = None
    shift: str | None = None


class BatchBase(BaseModel):
    batch_number: int = Field(..., gt=0)
    work_center_id: int = Field(..., gt=0)
    shift_start: datetime
    shift_end: datetime

    task_description: str = Field(default="", max_length=255)
    shift: str = Field(default="", max_length=50)
    team: str = Field(default="", max_length=100)
    batch_date: date | None = None
    nomenclature: str = Field(default="", max_length=255)
    ekn_code: str = Field(default="", max_length=100)

    @model_validator(mode="after")
    def fill_batch_date(self):
        if self.batch_date is None:
            self.batch_date = self.shift_start.date()
        return self


class BatchCreate(BatchBase):
    pass


class BatchCreateIn(BatchBase):
    pass


class BatchUpdate(BaseModel):
    batch_number: int | None = Field(default=None, gt=0)
    work_center_id: int | None = Field(default=None, gt=0)
    shift_start: datetime | None = None
    shift_end: datetime | None = None

    task_description: str | None = Field(default=None, max_length=255)
    shift: str | None = Field(default=None, max_length=50)
    team: str | None = Field(default=None, max_length=100)
    batch_date: date | None = None
    nomenclature: str | None = Field(default=None, max_length=255)
    ekn_code: str | None = Field(default=None, max_length=100)

    status: str | None = None
    is_closed: bool | None = None


class BatchRead(BatchBase):
    id: int
    status: str | None = None
    is_closed: bool | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class BatchListResponse(BaseModel):
    items: list[BatchRead]
    total: int


class AggregateSyncRequest(BaseModel):
    unique_codes: list[str] = Field(default_factory=list, min_length=1)


class AggregateAsyncRequest(BaseModel):
    unique_codes: list[str] = Field(default_factory=list, min_length=1)
    user_id: int | None = None


class BatchExportRequest(BaseModel):
    batch_ids: list[int] = Field(default_factory=list)
    format: Literal["csv", "xlsx"] = "xlsx"
    filters: BatchFilters = Field(default_factory=BatchFilters)


class BatchExportResponse(BaseModel):
    task_id: str
    status: str
    message: str | None = None


class BatchImportResponse(BaseModel):
    task_id: str
    status: str
    message: str | None = None


class BatchOperationResponse(BaseModel):
    success: bool
    message: str


class BatchIdResponse(BaseModel):
    id: int


class BatchIdsResponse(BaseModel):
    ids: list[int]