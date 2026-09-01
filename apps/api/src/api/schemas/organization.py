import uuid
from typing import Optional
from pydantic import BaseModel, ConfigDict


class OrganizationBase(BaseModel):
    name: str
    slug: str


class OrganizationCreate(BaseModel):
    name: str
    slug: Optional[str] = None  # Slug will be auto-generated from name if not provided


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None


class OrganizationResponse(OrganizationBase):
    id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)

class OrganizationMemberResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    is_active: bool
    is_superuser: bool
    role: str
    created_at: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)