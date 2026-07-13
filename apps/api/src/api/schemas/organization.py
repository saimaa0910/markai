import uuid
from typing import Optional
from pydantic import BaseModel


class OrganizationBase(BaseModel):
    name: str
    slug: str


class OrganizationCreate(BaseModel):
    name: str
    slug: Optional[str] = None  # Slug will be auto-generated from name if not provided


class OrganizationResponse(OrganizationBase):
    id: uuid.UUID

    class Config:
        from_attributes = True
