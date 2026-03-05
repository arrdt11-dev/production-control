from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class WorkCenterCreate(BaseModel):
    identifier: str = Field(..., max_length=50, min_length=1)
    name: str = Field(..., max_length=255, min_length=1)


class WorkCenterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
    name: str


class WorkCenterRef(BaseModel):
    """
    Короткая ссылка на РЦ (для вложенных ответов/связей).
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    identifier: str
