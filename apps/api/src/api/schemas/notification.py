import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from api.models.integration import NotificationChannel, NotificationPriority


# --- NOTIFICATION SCHEMAS ---

class NotificationBase(BaseModel):
    title: str
    body: str
    channel: Optional[NotificationChannel] = NotificationChannel.IN_APP
    priority: Optional[NotificationPriority] = NotificationPriority.MEDIUM
    event_type: Optional[str] = None
    action_url: Optional[str] = None
    meta_data: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    user_id: uuid.UUID


class NotificationResponse(NotificationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID
    is_read: bool

    class Config:
        from_attributes = True


# --- PREFERENCE SCHEMAS ---

class NotificationPreferenceBase(BaseModel):
    channel: NotificationChannel
    enabled: bool = True
    muted_event_types: Optional[List[str]] = None


class NotificationPreferenceUpdate(BaseModel):
    enabled: Optional[bool] = None
    muted_event_types: Optional[List[str]] = None


class NotificationPreferenceResponse(NotificationPreferenceBase):
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True
