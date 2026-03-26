from io import BytesIO

from minio import Minio

from app.settings import settings


class MinioService:
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_bucket_exists(self, bucket_name: str) -> None:
        if not self.client.bucket_exists(bucket_name):
            self.client.make_bucket(bucket_name)

    def upload_bytes(
        self,
        bucket_name: str,
        object_name: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> str:
        self.ensure_bucket_exists(bucket_name)

        data = BytesIO(content)
        self.client.put_object(
            bucket_name=bucket_name,
            object_name=object_name,
            data=data,
            length=len(content),
            content_type=content_type,
        )

        return self.get_public_url(bucket_name, object_name)

    def get_object(self, bucket_name: str, object_name: str):
        return self.client.get_object(bucket_name, object_name)

    def get_public_url(self, bucket_name: str, object_name: str) -> str:
        protocol = "https" if settings.minio_secure else "http"
        public_base_url = f"{protocol}://{settings.minio_public_endpoint}"
        return f"{public_base_url}/{bucket_name}/{object_name}"