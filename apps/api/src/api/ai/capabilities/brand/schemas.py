from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ToneViolation(BaseModel):
    sentence: str
    violated_rule: str
    suggested_rewrite: str

class BrandComplianceReport(BaseModel):
    brand_score: float = Field(..., description="Brand voice accuracy score from 0 to 100")
    tone_validated: bool = Field(..., description="True if tone satisfies rules")
    forbidden_words_found: List[str] = Field(default_factory=list, description="Prohibited vocabulary tags detected")
    tone_violations: List[ToneViolation] = Field(default_factory=list, description="Sentences breaching style voice guidelines")
    suggestions: List[str] = Field(default_factory=list, description="How to align the copy with target brand voice guidelines")
