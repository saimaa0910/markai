"""
EAIMOS Infrastructure DTOs
===========================
Pydantic v2 DTOs for Sprint 12 File Storage, Notifications & Feature Flags.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# File Asset DTOs
# =============================================================================

class UploadFileAssetDTO(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    file_type: str = Field(..., min_length=1, max_length=50)
    mime_type: Optional[str] = None
    file_size: int = Field(..., ge=0)
    storage_url: Optional[str] = None


class FileAssetResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    filename: str
    file_type: str
    mime_type: Optional[str] = None
    file_size: int
    storage_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Notification DTOs
# =============================================================================

class SendNotificationDTO(BaseModel):
    recipient: str = Field(..., min_length=1)
    channel: str = Field("EMAIL", description="EMAIL | SLACK | IN_APP | SMS")
    subject: str = Field(..., min_length=1)
    body: str = Field(..., min_length=1)


class NotificationResponseDTO(BaseModel):
    id: uuid.UUID
    recipient: str
    channel: str
    status: str = "DISPATCHED"
    sent_at: datetime


# =============================================================================
# Feature Flag DTOs
# =============================================================================

class CreateFeatureFlagDTO(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)
    is_enabled: bool = True
    strategy: str = Field("BOOLEAN", description="BOOLEAN | PERCENTAGE | TENANT_ALLOWLIST")


class FeatureFlagResponseDTO(BaseModel):
    id: uuid.UUID
    key: str
    name: str
    is_enabled: bool
    strategy: str
    created_at: datetime

    model_config = {"from_attributes": True}
