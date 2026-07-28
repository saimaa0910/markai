"""
EAIMOS Workflow & Agent DTOs
==============================
Pydantic v2 DTOs for Sprint 5 Workflows, Agents & Integrations Services.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# =============================================================================
# Workflow Definition & Execution DTOs
# =============================================================================

class CreateWorkflowDefinitionDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    trigger: str = Field("MANUAL", description="MANUAL | SCHEDULED | WEBHOOK | CAMPAIGN_EVENT")
    steps_definition: List[Dict[str, Any]] = Field(default_factory=list)
    cron_expression: Optional[str] = None
    max_retries: int = Field(3, ge=0, le=10)
    timeout_seconds: int = Field(3600, ge=1, le=86400)


class TriggerWorkflowDTO(BaseModel):
    workflow_id: uuid.UUID
    inputs: Dict[str, Any] = Field(default_factory=dict)


class WorkflowExecutionResponseDTO(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    status: str
    current_step: Optional[str] = None
    inputs: Dict[str, Any]
    outputs: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None


class WorkflowDefinitionResponseDTO(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    trigger: str
    steps_definition: Optional[List[Dict[str, Any]]] = None
    cron_expression: Optional[str] = None
    max_retries: int
    timeout_seconds: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# =============================================================================
# Agent Executor DTOs
# =============================================================================

class CreateAgentDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    role: str = Field(..., min_length=1, max_length=100)
    system_prompt: str = Field(..., min_length=1)
    tools: List[str] = Field(default_factory=list)


class ExecuteAgentTaskDTO(BaseModel):
    agent_id: uuid.UUID
    task_instructions: str = Field(..., min_length=1)
    context_data: Dict[str, Any] = Field(default_factory=dict)


class AgentTaskResultDTO(BaseModel):
    agent_id: uuid.UUID
    status: str
    output_text: str
    tool_calls_made: List[Dict[str, Any]] = Field(default_factory=list)
    execution_time_ms: float


# =============================================================================
# Integration & Webhook DTOs
# =============================================================================

class RegisterWebhookDTO(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    target_url: str = Field(..., min_length=1)
    events: List[str] = Field(..., min_items=1)
    secret_key: Optional[str] = None
