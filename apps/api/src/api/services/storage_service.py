"""
MinIO Object Storage Service
=============================
Provides production-grade MinIO object storage operations for EAIMOS:
- Bucket provisioning & management
- Object upload, download, and streaming
- Presigned preview/download URL generation
- Object deletion and cleanup
- SHA-256 integrity verification
"""
import io
import hashlib
import logging
from typing import Optional
from datetime import timedelta

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:
    Minio = None
    S3Error = Exception

from api.core.config import settings

logger = logging.getLogger(__name__)


class MinIOService:
    """Production MinIO Object Storage Manager."""

    _client: Optional[Minio] = None

    @classmethod
    def get_client(cls) -> Minio:
        """Initialize or return existing MinIO client instance."""
        if cls._client is None:
            # Strip protocol if specified in endpoint
            endpoint = settings.MINIO_ENDPOINT
            if endpoint.startswith("http://"):
                endpoint = endpoint[7:]
            elif endpoint.startswith("https://"):
                endpoint = endpoint[8:]

            cls._client = Minio(
                endpoint=endpoint,
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            cls.ensure_bucket_exists(settings.MINIO_BUCKET_NAME)
        return cls._client

    @classmethod
    def ensure_bucket_exists(cls, bucket_name: str = None) -> None:
        """Ensure default or target bucket exists in MinIO."""
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        try:
            client = cls._client or Minio(
                endpoint=settings.MINIO_ENDPOINT.replace("http://", "").replace("https://", ""),
                access_key=settings.MINIO_ACCESS_KEY,
                secret_key=settings.MINIO_SECRET_KEY,
                secure=settings.MINIO_SECURE,
            )
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
                logger.info(f"Created MinIO bucket: {bucket}")
        except Exception as e:
            logger.warning(f"MinIO bucket check failed (will retry on demand): {e}")

    @classmethod
    def upload_file(
        cls,
        file_bytes: bytes,
        object_name: str,
        content_type: str = "application/octet-stream",
        bucket_name: str = None,
    ) -> str:
        """
        Upload byte stream to MinIO object storage.
        Returns the object storage key.
        """
        client = cls.get_client()
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        data_stream = io.BytesIO(file_bytes)
        stream_len = len(file_bytes)

        try:
            client.put_object(
                bucket_name=bucket,
                object_name=object_name,
                data=data_stream,
                length=stream_len,
                content_type=content_type,
            )
            logger.info(f"Successfully uploaded {object_name} ({stream_len} bytes) to MinIO bucket {bucket}")
            return object_name
        except Exception as e:
            logger.error(f"Failed uploading object {object_name} to MinIO: {e}")
            raise RuntimeError(f"Storage upload failure: {e}")

    @classmethod
    def download_file_bytes(cls, object_name: str, bucket_name: str = None) -> bytes:
        """Download complete object content as byte array."""
        client = cls.get_client()
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        response = None
        try:
            response = client.get_object(bucket_name=bucket, object_name=object_name)
            return response.read()
        except Exception as e:
            logger.error(f"Failed downloading object {object_name} from MinIO: {e}")
            raise RuntimeError(f"Storage download failure: {e}")
        finally:
            if response:
                response.close()
                response.release_conn()

    @classmethod
    def get_presigned_url(
        cls,
        object_name: str,
        expires_seconds: int = 3600,
        bucket_name: str = None,
    ) -> str:
        """Generate presigned GET URL for object download/preview."""
        client = cls.get_client()
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        try:
            url = client.presigned_get_object(
                bucket_name=bucket,
                object_name=object_name,
                expires=timedelta(seconds=expires_seconds),
            )
            return url
        except Exception as e:
            logger.error(f"Failed generating presigned URL for {object_name}: {e}")
            # Fallback relative API endpoint
            return f"/api/v1/files/{object_name}/download"

    @classmethod
    def delete_file(cls, object_name: str, bucket_name: str = None) -> bool:
        """Delete object from MinIO storage."""
        client = cls.get_client()
        bucket = bucket_name or settings.MINIO_BUCKET_NAME
        try:
            client.remove_object(bucket_name=bucket, object_name=object_name)
            logger.info(f"Deleted object {object_name} from MinIO bucket {bucket}")
            return True
        except Exception as e:
            logger.error(f"Failed removing object {object_name} from MinIO: {e}")
            return False

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        """Calculate SHA-256 checksum for byte sequence."""
        return hashlib.sha256(data).hexdigest()
