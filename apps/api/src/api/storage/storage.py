"""
MinIO / S3 Object Storage Service Interface.
"""

from typing import BinaryIO, Optional


class ObjectStorageService:
    """
    MinIO S3-compatible Object Storage Manager.
    """
    def __init__(self, bucket_name: str = "eaimos-uploads") -> None:
        self.bucket_name = bucket_name

    async def upload_file(self, object_name: str, file_data: BinaryIO, content_type: str) -> str:
        """
        Upload binary file stream to object storage.
        """
        # TODO: Perform MinIO put_object operation
        return f"http://localhost:9000/{self.bucket_name}/{object_name}"

    async def get_presigned_url(self, object_name: str, expires_seconds: int = 3600) -> str:
        """
        Generate temporary presigned download URL.
        """
        # TODO: Perform MinIO presigned_get_object operation
        return f"http://localhost:9000/{self.bucket_name}/{object_name}?token=presigned"


storage_service = ObjectStorageService()
