from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class CompetitorFeatureItem(BaseModel):
    feature_name: str
    supported_by_us: bool
    competitor_support: Dict[str, bool] = Field(default_factory=dict)

class PricePoint(BaseModel):
    tier_name: str
    price: float
    billing_cycle: str = "monthly"

class CompetitorPricing(BaseModel):
    competitor_name: str
    plans: List[PricePoint] = Field(default_factory=list)

class SWOTMatrix(BaseModel):
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    threats: List[str] = Field(default_factory=list)

class ICPPersona(BaseModel):
    title: str
    industry: str
    pain_points: List[str] = Field(default_factory=list)
    tech_stack: List[str] = Field(default_factory=list)

class ResearchReportResponse(BaseModel):
    company_name: str
    swot: SWOTMatrix
    pestel: Dict[str, List[str]] = Field(default_factory=dict, description="Political, Economic, Social, Tech, Legal, Enviro")
    persona: ICPPersona
    competitors_pricing: List[CompetitorPricing] = Field(default_factory=list)
    feature_matrix: List[CompetitorFeatureItem] = Field(default_factory=list)
    executive_summary: str
