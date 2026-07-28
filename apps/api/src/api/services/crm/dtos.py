"""
EAIMOS CRM & Sales Pipeline DTOs
=================================
Pydantic v2 DTOs for Sprint 9 CRM & Sales Pipeline Services.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Pipeline & Stage DTOs
# =============================================================================

class CreatePipelineDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    currency: str = Field("USD", min_length=3, max_length=3)
    is_default: bool = False


class PipelineResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    currency: str
    is_default: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Deal DTOs
# =============================================================================

class CreateDealDTO(BaseModel):
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    title: str = Field(..., min_length=1, max_length=255)
    amount: float = Field(0.0, ge=0.0)
    contact_id: Optional[uuid.UUID] = None


class DealResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    pipeline_id: uuid.UUID
    stage_id: uuid.UUID
    title: str
    amount: float
    status: str = "OPEN"
    created_at: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Lead DTOs
# =============================================================================

class CreateLeadDTO(BaseModel):
    email: str = Field(..., min_length=3)
    full_name: str = Field(..., min_length=1)
    company_name: Optional[str] = None


class LeadResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    email: str
    full_name: str
    company_name: Optional[str] = None
    status: str = "NEW"
    lead_score: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}
