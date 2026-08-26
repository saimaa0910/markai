from typing import Optional, List
import uuid
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: Optional[bool] = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    org_name: Optional[str] = None  # Auto-created organization name
    invitation_token: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    id: uuid.UUID
    is_superuser: bool
    role: Optional[str] = None
    permissions: List[str] = []
    avatar: Optional[str] = None
    preferences: Optional[dict] = None

    class Config:
        from_attributes = True
        populate_by_name = True
