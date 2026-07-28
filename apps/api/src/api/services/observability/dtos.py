"""
EAIMOS Observability DTOs
==========================
Pydantic v2 DTOs for Sprint 11 Observability, Telemetry & Incident Monitoring.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Telemetry Trace DTOs
# =============================================================================

class RecordTraceDTO(BaseModel):
    trace_id: str = Field(..., min_length=1, max_length=64)
    span_id: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=255)
    start_time: datetime
    end_time: datetime
    status: str = Field("success", description="success | error")
    attributes: Dict[str, Any] = Field(default_factory=dict)


class TraceResponseDTO(BaseModel):
    id: uuid.UUID
    trace_id: str
    span_id: str
    name: str
    duration_ms: int
    status: str
    start_time: datetime
    end_time: datetime

    model_config = {"from_attributes": True}


# =============================================================================
# Log DTOs
# =============================================================================

class IngestLogDTO(BaseModel):
    level: str = Field("INFO", description="DEBUG | INFO | WARNING | ERROR | CRITICAL")
    logger: str = Field(..., min_length=1, max_length=100)
    message: str = Field(..., min_length=1)
    payload: Dict[str, Any] = Field(default_factory=dict)
    trace_id: Optional[str] = None


class LogResponseDTO(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    level: str
    logger: str
    message: str

    model_config = {"from_attributes": True}


# =============================================================================
# Incident & Alert DTOs
# =============================================================================

class CreateIncidentDTO(BaseModel):
    component: str = Field(..., min_length=1, max_length=100)
    service: str = Field(..., min_length=1, max_length=100)
    severity: str = Field("CRITICAL", description="WARNING | CRITICAL | OFFLINE")
    root_cause: str = Field(..., min_length=1)


class IncidentResponseDTO(BaseModel):
    id: uuid.UUID
    component: str
    service: str
    severity: str
    status: str = "active"
    root_cause: str
    start_time: datetime

    model_config = {"from_attributes": True}
