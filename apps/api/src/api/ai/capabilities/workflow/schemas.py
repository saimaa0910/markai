from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class WorkflowTrigger(BaseModel):
    event_source: str
    event_type: str
    parameters: Dict[str, Any] = Field(default_factory=dict)

class WorkflowStep(BaseModel):
    step_id: str
    action_type: str
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps that must execute first")
    retry_count: int = 3
    timeout: int = 60

class WorkflowTimelineSlot(BaseModel):
    slot_id: str
    steps: List[str] = Field(default_factory=list, description="Step IDs executing in parallel during this slot")
    estimated_start_sec: int
    duration_sec: int

class WorkflowResponse(BaseModel):
    name: str
    description: str
    trigger: WorkflowTrigger
    steps: List[WorkflowStep] = Field(default_factory=list)
    timeline: List[WorkflowTimelineSlot] = Field(default_factory=list)
    cycles_detected: bool = Field(..., description="True if infinite loops are detected")
    documentation: str
