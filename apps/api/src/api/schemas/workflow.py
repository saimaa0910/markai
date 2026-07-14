import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from api.models.workflow import WorkflowTrigger, WorkflowStatus, ExecutionStatus


# --- WORKFLOW DEFINITION SCHEMAS ---

class WorkflowDefinitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = WorkflowStatus.DRAFT
    trigger: Optional[WorkflowTrigger] = WorkflowTrigger.MANUAL
    steps_definition: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    cron_expression: Optional[str] = None
    webhook_config: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = 3
    timeout_seconds: Optional[int] = 3600


class WorkflowDefinitionCreate(WorkflowDefinitionBase):
    pass


class WorkflowDefinitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    trigger: Optional[WorkflowTrigger] = None
    steps_definition: Optional[List[Dict[str, Any]]] = None
    cron_expression: Optional[str] = None
    webhook_config: Optional[Dict[str, Any]] = None
    max_retries: Optional[int] = None
    timeout_seconds: Optional[int] = None


class WorkflowDefinitionResponse(WorkflowDefinitionBase):
    id: uuid.UUID
    organization_id: uuid.UUID

    class Config:
        from_attributes = True


# --- WORKFLOW EXECUTION SCHEMAS ---

class WorkflowExecutionCreate(BaseModel):
    input_data: Optional[Dict[str, Any]] = None


class WorkflowExecutionResponse(BaseModel):
    id: uuid.UUID
    workflow_id: uuid.UUID
    organization_id: uuid.UUID
    triggered_by: Optional[uuid.UUID] = None
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    latency_ms: Optional[int] = None

    class Config:
        from_attributes = True


# --- WORKFLOW STEP SCHEMAS ---

class WorkflowStepResponse(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    organization_id: uuid.UUID
    step_id: str
    step_type: str
    status: ExecutionStatus
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    latency_ms: Optional[int] = None

    class Config:
        from_attributes = True
