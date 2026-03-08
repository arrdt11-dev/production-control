from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    minio_endpoint: str = Field(alias="MINIO_ENDPOINT", default="production_s3:9000")
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY", default="minioadmin")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY", default="minioadmin")
    minio_secure: bool = Field(alias="MINIO_SECURE", default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()