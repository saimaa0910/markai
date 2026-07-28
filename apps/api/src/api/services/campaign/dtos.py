"""
EAIMOS Campaign & Content DTOs
================================
Pydantic v2 DTOs for Sprint 4 Campaign & Content Management Services.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Campaign DTOs
# =============================================================================

class CreateCampaignDTO(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    channel: str = Field("EMAIL", description="EMAIL | SOCIAL | ADS")
    goal: Optional[str] = None
    budget: float = Field(0.0, ge=0.0)
    currency: str = Field("USD", min_length=3, max_length=3)
    target_audience_id: Optional[uuid.UUID] = None
    scheduled_for: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)


class UpdateCampaignDTO(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[str] = None
    budget: Optional[float] = Field(None, ge=0.0)
    scheduled_for: Optional[datetime] = None
    tags: Optional[List[str]] = None


class CampaignResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    owner_id: Optional[uuid.UUID] = None
    title: str
    description: Optional[str] = None
    status: str
    channel: str
    goal: Optional[str] = None
    budget: float
    spent_budget: float
    currency: str
    target_audience_id: Optional[uuid.UUID] = None
    scheduled_for: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Audience Segment DTOs
# =============================================================================

class CreateAudienceSegmentDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    filters: Dict[str, Any] = Field(default_factory=dict)


class AudienceSegmentResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    filters: Dict[str, Any]
    estimated_reach: int
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Content Generation DTOs
# =============================================================================

class GenerateContentDTO(BaseModel):
    campaign_id: Optional[uuid.UUID] = None
    topic: str = Field(..., min_length=1)
    target_channel: str = Field("EMAIL")
    tone: str = Field("professional")
    target_audience_summary: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)


class GeneratedContentResponseDTO(BaseModel):
    title: str
    primary_content: str
    variants: List[str] = Field(default_factory=list)
    suggested_subject_lines: List[str] = Field(default_factory=list)
    estimated_read_time_min: float


# =============================================================================
# Variant DTOs
# =============================================================================

class CreateVariantDTO(BaseModel):
    campaign_id: uuid.UUID
    variant_name: str = Field(..., min_length=1, max_length=100) # e.g., "Variant A"
    content: str = Field(..., min_length=1)
    subject_line: Optional[str] = None


class VariantResponseDTO(BaseModel):
    id: uuid.UUID
    campaign_id: uuid.UUID
    variant_name: str
    content: str
    subject_line: Optional[str] = None
    click_count: int = 0
    impression_count: int = 0
    conversion_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
