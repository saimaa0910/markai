import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr
from api.models.lead import LeadStatus
from api.models.activity import ActivityType


# --- COMPANY SCHEMAS ---


class CompanyBase(BaseModel):
    name: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None


class CompanyCreate(CompanyBase):
    pass


class CompanyResponse(CompanyBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- CONTACT SCHEMAS ---


class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    job_title: Optional[str] = None
    company_id: Optional[uuid.UUID] = None


class ContactCreate(ContactBase):
    pass


class ContactResponse(ContactBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- LEAD SCHEMAS ---


class LeadBase(BaseModel):
    title: str
    status: Optional[LeadStatus] = LeadStatus.NEW
    value: Optional[float] = 0.00
    contact_id: Optional[uuid.UUID] = None
    company_id: Optional[uuid.UUID] = None


class LeadCreate(LeadBase):
    pass


class LeadResponse(LeadBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- ACTIVITY SCHEMAS ---


class ActivityBase(BaseModel):
    type: ActivityType
    title: str
    description: Optional[str] = None
    lead_id: Optional[uuid.UUID] = None
    contact_id: Optional[uuid.UUID] = None


class ActivityCreate(ActivityBase):
    pass


class ActivityResponse(ActivityBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True
