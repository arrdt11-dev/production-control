from __future__ import annotations

import os
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

    def ensure_bucket(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def ensure_all_buckets(self) -> None:
        for bucket_name in (
            settings.minio_bucket_reports,
            settings.minio_bucket_exports,
            settings.minio_bucket_imports,
        ):
            self.ensure_bucket(bucket_name)

    def upload_file(
        self,
        bucket: str,
        file_path: str,
        object_name: str,
        expires_days: int = 7,
    ) -> dict:
        self.ensure_bucket(bucket)

        self.client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
            content_type=self._get_content_type(file_path),
        )

        url = self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=expires_days),
        )


        url = url.replace(settings.minio_endpoint, settings.minio_public_endpoint)

        return {
            "bucket": bucket,
            "object_name": object_name,
            "file_url": url,
            "file_size": os.path.getsize(file_path),
        }

    def download_file(self, bucket: str, object_name: str, file_path: str) -> None:
        self.client.fget_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
        )

    def delete_file(self, bucket: str, object_name: str) -> None:
        self.client.remove_object(bucket, object_name)

    def list_files(self, bucket: str, prefix: str | None = None):
        return self.client.list_objects(
            bucket_name=bucket,
            prefix=prefix,
            recursive=True,
        )

    @staticmethod
    def _get_content_type(file_path: str) -> str:
        ext = os.path.splitext(file_path)[1].lower()
        content_types = {
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xls": "application/vnd.ms-excel",
            ".csv": "text/csv",
            ".pdf": "application/pdf",
            ".json": "application/json",
        }
        return content_types.get(ext, "application/octet-stream")