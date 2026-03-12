from __future__ import annotations

from datetime import timedelta

from minio import Minio

from app.settings import settings


class MinIOService:
    def __init__(self) -> None:
        self.client = Minio(
            settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def upload_file(self, bucket: str, file_path: str, object_name: str) -> str:
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

        self.client.fput_object(bucket, object_name, file_path)

        url = self.client.presigned_get_object(
            bucket,
            object_name,
            expires=timedelta(days=7),
        )

        return url