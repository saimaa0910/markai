import uuid
import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class FileAssetBase(BaseModel):
    filename: str
    file_type: str
    mime_type: Optional[str] = None
    file_size: int = 0
    storage_url: Optional[str] = None


class FileAssetCreate(FileAssetBase):
    pass


class FileAssetResponse(FileAssetBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime.datetime

    model_config = ConfigDict(from_attributes=True)