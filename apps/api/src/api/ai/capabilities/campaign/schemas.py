from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class AudienceSegment(BaseModel):
    segment_name: str
    description: str
    estimated_size: int

class ChannelAllocation(BaseModel):
    channel_name: str
    budget_percentage: float
    allocated_amount: float
    projected_clicks: int
    projected_leads: int

class CalendarEvent(BaseModel):
    launch_date: str
    channel: str
    task_name: str
    checklist_completed: bool

class CampaignReportResponse(BaseModel):
    objectives: List[str]
    segments: List[AudienceSegment] = Field(default_factory=list)
    allocations: List[ChannelAllocation] = Field(default_factory=list)
    total_budget: float
    total_projected_roi: float = Field(..., description="Projected Return on Investment percentage")
    calendar: List[CalendarEvent] = Field(default_factory=list)
    checklist: List[str] = Field(default_factory=list)
