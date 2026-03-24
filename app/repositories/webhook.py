from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator


ALLOWED_EVENTS = {
    "batch_created",
    "batch_closed",
    "report_generated",
}


class WebhookCreate(BaseModel):
    url: HttpUrl
    events: list[str] = Field(min_length=1)
    secret_key: str = Field(min_length=8, max_length=255)
    retry_count: int = Field(default=3, ge=0, le=10)
    timeout: int = Field(default=10, ge=1, le=120)

    @field_validator("events")
    @classmethod
    def validate_events(cls, value: list[str]) -> list[str]:
        if not value:
            raise ValueError("events must not be empty")

        invalid = [event for event in value if event not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(
                f"unsupported events: {', '.join(invalid)}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EVENTS))}"
            )

        return value

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("secret_key must not be empty")
        return value


class WebhookUpdate(BaseModel):
    url: HttpUrl | None = None
    events: list[str] | None = None
    secret_key: str | None = Field(default=None, min_length=8, max_length=255)
    is_active: bool | None = None
    retry_count: int | None = Field(default=None, ge=0, le=10)
    timeout: int | None = Field(default=None, ge=1, le=120)

    @field_validator("events")
    @classmethod
    def validate_events(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return value

        if not value:
            raise ValueError("events must not be empty")

        invalid = [event for event in value if event not in ALLOWED_EVENTS]
        if invalid:
            raise ValueError(
                f"unsupported events: {', '.join(invalid)}. "
                f"Allowed: {', '.join(sorted(ALLOWED_EVENTS))}"
            )

        return value

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str | None) -> str | None:
        if value is None:
            return value

        value = value.strip()
        if not value:
            raise ValueError("secret_key must not be empty")

        return value


class WebhookRead(BaseModel):
    id: int
    url: str
    events: list[str]
    is_active: bool
    retry_count: int
    timeout: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryRead(BaseModel):
    id: int
    subscription_id: int
    event_type: str
    payload: dict
    status: str
    attempts: int
    response_status: int | None
    response_body: str | None
    error_message: str | None
    created_at: datetime
    delivered_at: datetime | None

    model_config = {"from_attributes": True}


class WebhookListResponse(BaseModel):
    items: list[WebhookRead]
    total: int


class WebhookDeliveryListResponse(BaseModel):
    items: list[WebhookDeliveryRead]
    total: int