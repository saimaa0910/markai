import uuid
import logging
from sqlalchemy.orm import Session
from api.models.file_asset import FileAsset
from api.services.storage_service import MinIOService

logger = logging.getLogger(__name__)


class AssetManager:
    """
    Manages generated images, saving bytes to the MinIO object store,
    and registering them as FileAssets in the database.
    """

    @staticmethod
    def save_image_asset(
        db: Session,
        image_bytes: bytes,
        filename: str,
        organization_id: uuid.UUID,
    ) -> FileAsset:
        """
        Saves image bytes as a FileAsset.
        Returns:
            FileAsset database model instance.
        """
        file_id = uuid.uuid4()
        
        # Determine name & type
        ext = filename.split(".")[-1] if "." in filename else "png"
        local_filename = f"{file_id}.{ext}"
        
        # 1. Upload to MinIO object storage
        MinIOService.upload_file(
            file_bytes=image_bytes,
            object_name=local_filename,
            content_type="image/png"
        )
        
        # 2. Get relative download/view URL
        storage_url = f"/api/v1/files/{file_id}/download"
        
        # 3. Create FileAsset DB record
        file_asset = FileAsset(
            id=file_id,
            filename=filename,
            file_type=ext.upper(),
            mime_type="image/png",
            file_size=len(image_bytes),
            storage_url=storage_url,
            organization_id=organization_id,
        )
        
        db.add(file_asset)
        db.commit()
        db.refresh(file_asset)
        
        logger.info("Created FileAsset entry %s for generated image", file_id)
        return file_asset
