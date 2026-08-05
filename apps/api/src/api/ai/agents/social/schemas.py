"""
Social Agent Schemas — Sprint 7.5
====================================
Pydantic request/response models for all Social Agent API endpoints.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from api.ai.agents.social.constants import (
    SocialPlatform,
    SocialContentType,
    ScheduleType,
    SocialPostStatus,
    EngagementType,
)


# ─── Common Sub-models ────────────────────────────────────────────────────────

class HashtagItem(BaseModel):
    tag: str
    category: str
    reach_score: float


class HashtagResult(BaseModel):
    hashtags: List[HashtagItem]
    hashtag_string: str
    total_count: int
    estimated_reach: float
    categories: Dict[str, List[str]]


class PlatformOptimizationResult(BaseModel):
    optimized_content: str
    platform: str
    tone: str
    char_used: int
    char_limit: int
    char_remaining: int
    within_limit: bool
    best_practices: List[str]


class SocialReflectionResult(BaseModel):
    is_satisfactory: bool
    platform_compliant: bool
    brand_compliant: bool
    readability_ok: bool
    engagement_score: float
    cta_quality: float
    hook_quality: float
    formatting_ok: bool
    critique: Optional[str] = None
    suggested_edits: Optional[str] = None


class SocialEvaluationResult(BaseModel):
    brand_score: float
    engagement_score: float
    platform_score: float
    readability: float
    seo_score: float
    viral_potential: float
    confidence: float
    overall_score: float
    passed: bool
    critique: Optional[str] = None


class ScheduleMetadata(BaseModel):
    schedule_type: ScheduleType = ScheduleType.DRAFT
    scheduled_at: Optional[datetime] = None
    timezone: Optional[str] = "UTC"
    recurring_pattern: Optional[str] = None  # e.g. "every_monday_9am"


# ─── Generate ─────────────────────────────────────────────────────────────────

class SocialGenerateRequest(BaseModel):
    platform: SocialPlatform
    content_type: SocialContentType
    prompt: str = Field(..., description="Topic or brief for the social post")

    # Context
    target_audience: Optional[str] = Field(None, description="Target audience persona")
    keywords: Optional[List[str]] = Field(None, description="SEO/hashtag keywords")
    campaign_id: Optional[uuid.UUID] = Field(None, description="Link to campaign context")
    brand_voice_override: Optional[str] = Field(None, description="Override org brand voice")
    knowledge_collections: Optional[List[uuid.UUID]] = Field(None, description="Knowledge collections to search")

    # Generation flags
    generate_image: Optional[bool] = Field(None, description="Force image generation on/off")
    image_style: Optional[str] = Field(None, description="Image style preset")
    translate_to: Optional[str] = Field(None, description="Translate output to language code")

    # Schedule
    schedule: Optional[ScheduleMetadata] = None

    # LLM overrides
    preferred_model: Optional[str] = None
    temperature: Optional[float] = 0.75

    # Pipeline flags
    run_reflection: bool = True
    run_evaluation: bool = True


class SocialStreamRequest(SocialGenerateRequest):
    session_id: Optional[uuid.UUID] = None
    session_title: Optional[str] = "Social Studio Session"


# ─── Schedule ─────────────────────────────────────────────────────────────────

class SocialScheduleRequest(BaseModel):
    post_run_id: str = Field(..., description="AgentRun ID containing generated post")
    platform: SocialPlatform
    schedule: ScheduleMetadata
    auto_publish: bool = False


# ─── Publish ──────────────────────────────────────────────────────────────────

class SocialPublishRequest(BaseModel):
    post_run_id: str = Field(..., description="AgentRun ID to publish")
    platform: SocialPlatform
    override_content: Optional[str] = Field(None, description="Manual content override before publishing")
    image_url: Optional[str] = Field(None, description="Final image URL to publish with")


# ─── Reply / Engagement ───────────────────────────────────────────────────────

class SocialReplyRequest(BaseModel):
    platform: SocialPlatform
    original_post: str = Field(..., description="The post or comment being replied to")
    engagement_type: EngagementType = EngagementType.REPLY
    brand_voice_override: Optional[str] = None
    preferred_model: Optional[str] = None
    temperature: Optional[float] = 0.7


# ─── Optimize ─────────────────────────────────────────────────────────────────

class SocialOptimizeRequest(BaseModel):
    content: str = Field(..., description="Raw content to optimize")
    platform: SocialPlatform
    hashtag_string: Optional[str] = None
    cta: Optional[str] = None
    hook: Optional[str] = None


# ─── Hashtags ─────────────────────────────────────────────────────────────────

class SocialHashtagRequest(BaseModel):
    platform: SocialPlatform
    keywords: Optional[List[str]] = None
    industry: Optional[str] = None
    brand_name: Optional[str] = None
    campaign_name: Optional[str] = None
    location: Optional[str] = None
    max_count: Optional[int] = None


# ─── Response Models ──────────────────────────────────────────────────────────

class SocialPostContent(BaseModel):
    caption: Optional[str] = None
    headline: Optional[str] = None
    cta: Optional[str] = None
    hook: Optional[str] = None
    body: Optional[str] = None
    summary: Optional[str] = None
    thread_parts: Optional[List[str]] = None
    raw_content: str


class SocialPostResponse(BaseModel):
    run_id: Optional[str] = None
    platform: str
    content_type: str
    content: SocialPostContent
    image_url: Optional[str] = None
    hashtags: Optional[HashtagResult] = None
    optimization: Optional[PlatformOptimizationResult] = None
    reflection: Optional[SocialReflectionResult] = None
    evaluation: Optional[SocialEvaluationResult] = None
    plan: Optional[Dict[str, Any]] = None
    schedule: Optional[ScheduleMetadata] = None
    total_tokens: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0


class SocialScheduleResponse(BaseModel):
    run_id: str
    platform: str
    status: SocialPostStatus
    scheduled_at: Optional[datetime] = None
    schedule_type: ScheduleType
    message: str


class SocialPublishResponse(BaseModel):
    run_id: str
    platform: str
    status: str
    published: bool
    message: str
    platform_post_id: Optional[str] = None


class SocialReplyResponse(BaseModel):
    engagement_type: str
    platform: str
    reply_content: str
    total_tokens: int = 0
    latency_ms: int = 0


class SocialPlatformInfo(BaseModel):
    platform: str
    char_limit: int
    hashtag_limit: int
    tone: str
    emoji_friendly: bool
    supports_images: bool
    supports_video: bool
    supports_carousel: bool
    supports_polls: bool
    best_practices: List[str]
    image_ratio: Optional[str] = None


class SocialHistoryItem(BaseModel):
    run_id: str
    platform: str
    content_type: str
    status: str
    output_preview: str
    image_url: Optional[str] = None
    latency_ms: Optional[int] = None
    tokens: int = 0
    created_at: Optional[str] = None
    scheduled_at: Optional[str] = None


class SocialCalendarResponse(BaseModel):
    view: str  # "daily" | "weekly" | "monthly"
    entries: List[Dict[str, Any]]
    total_posts: int


class SocialAnalyticsResponse(BaseModel):
    platform: Optional[str] = None
    total_posts: int
    avg_tokens: float
    avg_latency_ms: float
    top_content_types: List[str]
    recent_runs: List[Dict[str, Any]]


class SocialQueueItem(BaseModel):
    run_id: str
    platform: str
    content_type: str
    status: str
    scheduled_at: Optional[str] = None
    preview: str


class SocialQueueResponse(BaseModel):
    queue: List[SocialQueueItem]
    total: int
    draft_count: int
    scheduled_count: int
