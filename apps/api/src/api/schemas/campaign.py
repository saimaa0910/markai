import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from api.models.campaign import CampaignStatus, CampaignChannel


# --- Campaign Template Schemas ---
class CampaignTemplateBase(BaseModel):
    title: str = Field(..., max_length=255)
    subject: Optional[str] = Field(None, max_length=255)
    content_a: str
    content_b: Optional[str] = None


class CampaignTemplateCreate(CampaignTemplateBase):
    pass


class CampaignTemplateResponse(CampaignTemplateBase):
    id: uuid.UUID
    campaign_id: uuid.UUID
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# --- Campaign Analytics Schemas ---
class CampaignAnalyticsResponse(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    impressions_a: int
    clicks_a: int
    conversions_a: int
    impressions_b: int
    clicks_b: int
    conversions_b: int
    revenue: float
    organization_id: uuid.UUID

    model_config = ConfigDict(from_attributes=True)


# --- Campaign Schemas ---
class CampaignBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    budget: float = Field(0.00, ge=0.0)
    channel: CampaignChannel
    scheduled_for: Optional[datetime] = None


class CampaignCreate(CampaignBase):
    template: CampaignTemplateCreate


class CampaignUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0.0)
    channel: Optional[CampaignChannel] = None
    status: Optional[CampaignStatus] = None
    scheduled_for: Optional[datetime] = None


class CampaignResponse(CampaignBase):
    id: uuid.UUID
    status: CampaignStatus
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    template: Optional[CampaignTemplateResponse] = None
    analytics: Optional[CampaignAnalyticsResponse] = None

    model_config = ConfigDict(from_attributes=True)


# --- Tracking Schema ---
class CampaignTrackRequest(BaseModel):
    variant: str = Field(..., pattern="^[ABab]$")
    event_type: str = Field(..., pattern="^(impression|click|conversion)$")
    revenue_generated: float = Field(0.00, ge=0.0)
