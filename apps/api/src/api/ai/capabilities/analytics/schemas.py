from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CohortData(BaseModel):
    cohort_month: str
    starting_users: int
    retention_rates: Dict[str, float] = Field(default_factory=dict, description="Percentage retained monthly")

class AnomalyLog(BaseModel):
    metric_name: str
    date: str
    value: float
    z_score: float
    details: str

class LeadFunnelStage(BaseModel):
    stage_name: str
    volume: int
    conversion_rate_to_next: float

class AnalyticsReportResponse(BaseModel):
    ltv_cac_ratio: float = Field(..., description="Customer lifetime value to acquisition cost ratio")
    roas: float = Field(..., description="Return on Ad Spend ratio")
    revenue_forecast: List[float] = Field(default_factory=list, description="Projected monthly revenues")
    lead_funnel: List[LeadFunnelStage] = Field(default_factory=list)
    cohort_retention: List[CohortData] = Field(default_factory=list)
    anomalies: List[AnomalyLog] = Field(default_factory=list)
    executive_insights: List[str] = Field(default_factory=list)
