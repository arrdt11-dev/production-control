from datetime import date, datetime
from pydantic import BaseModel, Field

from app.schemas.product import ProductRead


class BatchCreateIn(BaseModel):
    # вход как в ТЗ (русские поля)
    is_closed: bool = Field(default=False, validation_alias="СтатусЗакрытия")
    task_description: str = Field(validation_alias="ПредставлениеЗаданияНаСмену")
    work_center_name: str = Field(validation_alias="РабочийЦентр")
    shift: str = Field(validation_alias="Смена")
    team: str = Field(validation_alias="Бригада")

    batch_number: int = Field(validation_alias="НомерПартии")
    batch_date: date = Field(validation_alias="ДатаПартии")

    nomenclature: str = Field(validation_alias="Номенклатура")
    ekn_code: str = Field(validation_alias="КодЕКН")

    work_center_identifier: str = Field(validation_alias="ИдентификаторРЦ")

    shift_start: datetime = Field(validation_alias="ДатаВремяНачалаСмены")
    shift_end: datetime = Field(validation_alias="ДатаВремяОкончанияСмены")


class BatchUpdate(BaseModel):
    # обновление партии
    is_closed: bool | None = None
    task_description: str | None = None
    shift: str | None = None
    team: str | None = None
    nomenclature: str | None = None
    ekn_code: str | None = None
    shift_start: datetime | None = None
    shift_end: datetime | None = None


class BatchRead(BaseModel):
    id: int
    is_closed: bool
    closed_at: datetime | None

    task_description: str
    work_center_id: int
    shift: str
    team: str

    batch_number: int
    batch_date: date

    nomenclature: str
    ekn_code: str

    shift_start: datetime
    shift_end: datetime

    products: list[ProductRead] = []

    model_config = {"from_attributes": True}


class AggregateSyncRequest(BaseModel):
    unique_codes: list[str]
