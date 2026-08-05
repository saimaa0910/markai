"""
Content Agent API Schemas — Sprint 7.2
=======================================
Pydantic schemas for content generation, improvement, translation, and SEO checks.
"""
import uuid
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from api.ai.agents.content.constants import ContentType, ImprovementType


class ContentGenerateRequest(BaseModel):
    content_type: ContentType
    prompt: str = Field(..., description="Details of what content to write")
    
    # Custom Brand Settings (Optional overrides to Organization memories)
    brand_voice_override: Optional[str] = Field(None, description="Custom brand tone/rules")
    forbidden_words: Optional[List[str]] = Field(None, description="Words to explicitly avoid")
    preferred_words: Optional[List[str]] = Field(None, description="Words to explicitly use")
    
    # Context / RAG
    knowledge_collections: Optional[List[uuid.UUID]] = Field(None, description="Search specified vector spaces")
    target_audience: Optional[str] = Field(None, description="Target demographic (e.g. 'C-Suite', 'SaaS founders')")
    keywords: Optional[List[str]] = Field(None, description="Keywords to optimize SEO for")
    
    # Run configuration overrides
    preferred_model: Optional[str] = None
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    
    # Flag constraints
    run_reflection: bool = True
    run_evaluation: bool = True


class ContentStreamRequest(ContentGenerateRequest):
    session_id: Optional[uuid.UUID] = None
    session_title: Optional[str] = "Content Generation Stream"


class ContentImproveRequest(BaseModel):
    content: str = Field(..., description="The raw content to improve")
    improvement_type: ImprovementType
    
    # Parameter modifiers depending on improvement_type
    target_tone: Optional[str] = Field(None, description="Target tone for tone conversion")
    target_audience: Optional[str] = Field(None, description="Target audience mapping")
    target_language: Optional[str] = Field(None, description="Target language code for translation")
    keywords: Optional[List[str]] = Field(None, description="Keywords for SEO optimization")
    
    # Gateway overrides
    preferred_model: Optional[str] = None
    temperature: Optional[float] = 0.5


class ContentSEOMetrics(BaseModel):
    title_length_ok: bool
    description_length_ok: bool
    keyword_density: Dict[str, float]
    keyword_density_ok: bool
    heading_hierarchy_ok: bool
    readability_score: float
    readability_level: str
    internal_links_count: int
    external_links_count: int
    seo_score: float
    suggestions: List[str]


class ContentResponse(BaseModel):
    title: str
    generated_content: str
    plan: Optional[Dict[str, Any]] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    total_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    seo_metrics: Optional[ContentSEOMetrics] = None
    overall_score: Optional[float] = None
    reflection_passed: bool = True
    critique: Optional[str] = None
    suggested_edits: Optional[str] = None


class ContentTemplateResponse(BaseModel):
    id: str
    name: str
    description: str
    content_type: ContentType
    template_text: str
    required_variables: List[str]
