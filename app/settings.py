from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    redis_url: str = Field(alias="REDIS_URL")
    celery_broker_url: str = Field(alias="CELERY_BROKER_URL")
    celery_result_backend: str = Field(alias="CELERY_RESULT_BACKEND")

    minio_endpoint: str = Field(alias="MINIO_ENDPOINT", default="production_s3:9000")
    minio_public_endpoint: str = Field(
        alias="MINIO_PUBLIC_ENDPOINT",
        default="localhost:9000",
    )
    minio_access_key: str = Field(alias="MINIO_ACCESS_KEY", default="minioadmin")
    minio_secret_key: str = Field(alias="MINIO_SECRET_KEY", default="minioadmin")
    minio_secure: bool = Field(alias="MINIO_SECURE", default=False)

    minio_bucket_reports: str = Field(alias="MINIO_BUCKET_REPORTS", default="reports")
    minio_bucket_exports: str = Field(alias="MINIO_BUCKET_EXPORTS", default="exports")
    minio_bucket_imports: str = Field(alias="MINIO_BUCKET_IMPORTS", default="imports")

    api_key: str = Field(alias="API_KEY", default="supersecret123")

    db_pool_size: int = Field(alias="DB_POOL_SIZE", default=10)
    db_max_overflow: int = Field(alias="DB_MAX_OVERFLOW", default=20)
    db_pool_recycle: int = Field(alias="DB_POOL_RECYCLE", default=3600)

    max_upload_file_size: int = Field(
        alias="MAX_UPLOAD_FILE_SIZE",
        default=50 * 1024 * 1024,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )


settings = Settings()