from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class KeywordGapItem(BaseModel):
    keyword: str
    search_volume: int
    difficulty: float
    competitor_rank: int
    gap_score: float

class FAQItem(BaseModel):
    question: str
    answer: str

class SEOResultSchema(BaseModel):
    score: float = Field(..., description="SEO score from 0 to 100")
    readability_score: float = Field(..., description="Flesch-Kincaid ease grade")
    keyword_density: Dict[str, float] = Field(default_factory=dict, description="Word count percentage")
    suggestions: List[str] = Field(default_factory=list, description="Concrete optimization suggestions")
    headings: List[str] = Field(default_factory=list, description="Constructed H1, H2, H3 tags list")
    schema_markup: Dict[str, Any] = Field(default_factory=dict, description="JSON-LD schema org representation")
    meta_title: str = Field(..., description="SEO Title tag suggestions")
    meta_description: str = Field(..., description="160 character description metadata")
    gap_analysis: List[KeywordGapItem] = Field(default_factory=list, description="Missing competitor search tags")
    faq: List[FAQItem] = Field(default_factory=list, description="Common schema FAQs")
