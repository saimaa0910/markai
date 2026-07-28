"""
EAIMOS Platform DTOs
=====================
Pydantic v2 DTOs for Sprint 6 Billing, Analytics & Security Platform Services.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Billing DTOs
# =============================================================================

class CreateSubscriptionDTO(BaseModel):
    plan_tier: str = Field("STARTER", description="FREE | STARTER | PROFESSIONAL | ENTERPRISE")
    billing_cycle: str = Field("MONTHLY", description="MONTHLY | ANNUAL")
    stripe_token: Optional[str] = None


class SubscriptionResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    plan_tier: str
    billing_cycle: str
    status: str = "ACTIVE"
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool = False

    model_config = {"from_attributes": True}


class AddCreditsDTO(BaseModel):
    amount: float = Field(..., gt=0.0)
    description: str = Field(..., min_length=1)


class CreditBalanceResponseDTO(BaseModel):
    organization_id: uuid.UUID
    balance: float
    currency: str = "USD"


# =============================================================================
# Analytics DTOs
# =============================================================================

class AnalyticsQueryDTO(BaseModel):
    metric: str = Field(..., min_length=1)
    period: str = Field("DAY")
    start_date: datetime
    end_date: datetime


class AnalyticsSummaryDTO(BaseModel):
    metric: str
    total_value: float
    data_points: List[Dict[str, Any]] = Field(default_factory=list)


# =============================================================================
# Security Platform DTOs
# =============================================================================

class ReportIncidentDTO(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    severity: str = Field("MEDIUM", description="LOW | MEDIUM | HIGH | CRITICAL")
    description: str = Field(..., min_length=1)


class SecurityIncidentResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    title: str
    severity: str
    status: str = "OPEN"
    description: str
    reported_at: datetime
