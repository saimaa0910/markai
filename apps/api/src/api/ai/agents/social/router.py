"""
Social Agent API Router — Sprint 7.5
=======================================
15 REST endpoints for the Enterprise Social Media Agent.
Follows the identical pattern established by Content Agent and Image Agent routers.
"""
import uuid
import json
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentType, AgentStatus
from api.ai.agents.social.schemas import (
    SocialGenerateRequest,
    SocialStreamRequest,
    SocialScheduleRequest,
    SocialPublishRequest,
    SocialReplyRequest,
    SocialOptimizeRequest,
    SocialHashtagRequest,
    SocialPostResponse,
    SocialScheduleResponse,
    SocialPublishResponse,
    SocialReplyResponse,
    SocialPlatformInfo,
    SocialHistoryItem,
    SocialCalendarResponse,
    SocialAnalyticsResponse,
    SocialQueueResponse,
    SocialQueueItem,
)
from api.ai.agents.social.service import SocialAgentService
from api.ai.agents.social.helpers import HashtagEngine, PlatformOptimizer, get_publisher
from api.ai.agents.social.validators import validate_social_input, validate_publish_request
from api.ai.agents.social.constants import PLATFORM_CONFIGS, SocialPlatform, SocialContentType

router = APIRouter(prefix="/social", tags=["social-agent"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


# ─── Session Resolution ───────────────────────────────────────────────────────

def _resolve_social_session(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> AgentSession:
    """Finds or creates the persistent session dedicated to the Social agent."""
    agent = db.scalars(
        select(AgentDefinition).where(
            AgentDefinition.organization_id == org_id,
            AgentDefinition.agent_type == AgentType.SOCIAL,
            AgentDefinition.status == AgentStatus.ACTIVE,
        )
    ).first()

    if not agent:
        agent = AgentDefinition(
            name="Social Media Agent Studio",
            description="Enterprise Social Media Agent — Full Lifecycle",
            agent_type=AgentType.SOCIAL,
            status=AgentStatus.ACTIVE,
            allowed_tools=[
                "knowledge_tool", "image_generation_tool", "campaign_tool",
                "analytics_tool", "brand_tool", "web_search_tool",
                "email_tool", "calendar_tool",
            ],
            organization_id=org_id,
            memory_enabled=True,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

    session = db.scalars(
        select(AgentSession).where(
            AgentSession.agent_id == agent.id,
            AgentSession.organization_id == org_id,
            AgentSession.is_active.is_(True),
        )
    ).first()

    if not session:
        session = AgentSession(
            agent_id=agent.id,
            user_id=user_id,
            organization_id=org_id,
            title="Social Studio Session",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    return session


def _resolve_social_session_by_id(db: Session, org_id: uuid.UUID, user_id: uuid.UUID, agent_id: Optional[uuid.UUID] = None) -> AgentSession:
    if not agent_id:
        return _resolve_social_session(db, org_id, user_id)
        
    session = db.scalars(
        select(AgentSession).where(
            AgentSession.agent_id == agent_id,
            AgentSession.organization_id == org_id,
            AgentSession.is_active == True,
        )
    ).first()
    
    if not session:
        session = AgentSession(
            agent_id=agent_id,
            user_id=user_id,
            organization_id=org_id,
            title="Social Studio Session",
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        
    return session


# ─── POST /generate ───────────────────────────────────────────────────────────

@router.post("/generate", status_code=status.HTTP_200_OK)
def generate_social_post(
    payload: SocialGenerateRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Generate a complete social media post synchronously."""
    validate_social_input(payload.prompt, payload.platform, payload.keywords)
    session = _resolve_social_session_by_id(db, membership.organization_id, membership.user_id, payload.agent_id)

    result = SocialAgentService.generate_social(
        db=db,
        session=session,
        platform=payload.platform,
        content_type=payload.content_type,
        prompt=payload.prompt,
        target_audience=payload.target_audience,
        keywords=payload.keywords,
        campaign_id=payload.campaign_id,
        brand_voice_override=payload.brand_voice_override,
        knowledge_collections=payload.knowledge_collections,
        generate_image=payload.generate_image,
        image_style=payload.image_style,
        translate_to=payload.translate_to,
        preferred_model=payload.preferred_model,
        temperature=payload.temperature or 0.75,
        run_reflection=payload.run_reflection,
        run_evaluation=payload.run_evaluation,
    )
    return result


# ─── POST /stream ─────────────────────────────────────────────────────────────

@router.post("/stream")
def stream_social_post(
    payload: SocialStreamRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> StreamingResponse:
    """Generate a social media post with real-time SSE streaming."""
    validate_social_input(payload.prompt, payload.platform, payload.keywords)

    if payload.session_id:
        session = db.scalars(
            select(AgentSession).where(
                AgentSession.id == payload.session_id,
                AgentSession.organization_id == membership.organization_id,
            )
        ).first()
        if not session:
            raise HTTPException(status_code=404, detail="Social session not found.")
    else:
        session = _resolve_social_session_by_id(db, membership.organization_id, membership.user_id, payload.agent_id)

    def event_generator():
        yield from SocialAgentService.stream_social(
            db=db,
            session=session,
            platform=payload.platform,
            content_type=payload.content_type,
            prompt=payload.prompt,
            target_audience=payload.target_audience,
            keywords=payload.keywords,
            campaign_id=payload.campaign_id,
            brand_voice_override=payload.brand_voice_override,
            knowledge_collections=payload.knowledge_collections,
            generate_image=payload.generate_image,
            image_style=payload.image_style,
            translate_to=payload.translate_to,
            preferred_model=payload.preferred_model,
            temperature=payload.temperature or 0.75,
            run_reflection=payload.run_reflection,
            run_evaluation=payload.run_evaluation,
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ─── POST /schedule ───────────────────────────────────────────────────────────

@router.post("/schedule", response_model=SocialScheduleResponse)
def schedule_post(
    payload: SocialScheduleRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Schedule a generated social post for future publishing."""
    from api.ai.agents.social.agent import social_agent

    result = social_agent.schedule_post(
        db=db,
        run_id=payload.post_run_id,
        platform=payload.platform,
        schedule_type=payload.schedule.schedule_type.value,
        scheduled_at=payload.schedule.scheduled_at,
        timezone=payload.schedule.timezone or "UTC",
        recurring_pattern=payload.schedule.recurring_pattern,
        auto_publish=payload.auto_publish,
    )

    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result


# ─── POST /publish ────────────────────────────────────────────────────────────

@router.post("/publish", response_model=SocialPublishResponse)
def publish_post(
    payload: SocialPublishRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Publish a social post to the target platform via adapter."""
    if payload.override_content:
        validate_publish_request(payload.platform.value, payload.override_content, payload.image_url)

    from api.ai.agents.social.agent import social_agent
    result = social_agent.publish_post(
        db=db,
        run_id=payload.post_run_id,
        platform=payload.platform,
        override_content=payload.override_content,
        image_url=payload.image_url,
    )
    return result


# ─── POST /reply ──────────────────────────────────────────────────────────────

@router.post("/reply", response_model=SocialReplyResponse)
def generate_reply(
    payload: SocialReplyRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Generate an engagement reply, comment, or DM draft via ContentAgent."""
    import time
    start = time.perf_counter()

    from api.ai.agents.social.agent import social_agent
    session = _resolve_social_session(db, membership.organization_id, membership.user_id)

    reply = social_agent.generate_reply(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        platform=payload.platform,
        original_post=payload.original_post,
        engagement_type=payload.engagement_type,
        brand_voice_override=payload.brand_voice_override,
        preferred_model=payload.preferred_model,
        temperature=payload.temperature or 0.7,
    )

    latency_ms = int((time.perf_counter() - start) * 1000)
    return {
        "engagement_type": payload.engagement_type.value,
        "platform": payload.platform.value,
        "reply_content": reply,
        "total_tokens": 0,
        "latency_ms": latency_ms,
    }


# ─── POST /optimize ───────────────────────────────────────────────────────────

@router.post("/optimize")
def optimize_content(
    payload: SocialOptimizeRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Apply platform-specific formatting and optimization to raw content."""
    result = PlatformOptimizer.optimize(
        content=payload.content,
        platform=payload.platform.value,
        hashtag_string=payload.hashtag_string or "",
        cta=payload.cta,
        hook=payload.hook,
    )
    return result


# ─── POST /hashtags ───────────────────────────────────────────────────────────

@router.post("/hashtags")
def generate_hashtags(
    payload: SocialHashtagRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Generate AI-ranked hashtags for a platform and topic."""
    result = HashtagEngine.generate(
        platform=payload.platform.value,
        keywords=payload.keywords,
        industry=payload.industry,
        brand_name=payload.brand_name,
        campaign_name=payload.campaign_name,
        location=payload.location,
        max_count=payload.max_count,
    )
    return result


# ─── GET /history ─────────────────────────────────────────────────────────────

@router.get("/history", response_model=List[SocialHistoryItem])
def get_history(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    limit: int = Query(20, ge=1, le=100),
    platform: Optional[str] = Query(None, description="Filter by platform"),
) -> Any:
    """List recent social post generation runs for this organization."""
    session = _resolve_social_session(db, membership.organization_id, membership.user_id)

    query = (
        select(AgentRun)
        .where(
            AgentRun.session_id == session.id,
            AgentRun.deleted_at.is_(None),
        )
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    runs = db.scalars(query).all()

    results = []
    for r in runs:
        plan = r.plan or {}
        meta = plan.get("metadata", {})
        run_platform = meta.get("platform", "")
        if platform and run_platform.upper() != platform.upper():
            continue
        output_preview = ""
        if r.agent_output:
            try:
                content_obj = json.loads(r.agent_output)
                output_preview = content_obj.get("raw_content", "")[:200]
            except Exception:
                output_preview = str(r.agent_output)[:200]

        schedule = plan.get("schedule", {})
        results.append(SocialHistoryItem(
            run_id=str(r.id),
            platform=run_platform or "UNKNOWN",
            content_type=meta.get("content_type", "POST"),
            status=r.status.value if hasattr(r.status, "value") else str(r.status),
            output_preview=output_preview,
            latency_ms=r.latency_ms,
            tokens=r.total_tokens,
            created_at=r.created_at.isoformat() if r.created_at else None,
            scheduled_at=schedule.get("scheduled_at"),
        ))

    return results


# ─── GET /calendar ────────────────────────────────────────────────────────────

@router.get("/calendar")
def get_calendar(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    view: str = Query("weekly", regex="^(daily|weekly|monthly)$"),
) -> Any:
    """Return a calendar view of scheduled social posts."""
    from api.ai.agents.social.helpers import SocialCalendar

    session = _resolve_social_session(db, membership.organization_id, membership.user_id)
    runs = db.scalars(
        select(AgentRun)
        .where(AgentRun.session_id == session.id, AgentRun.deleted_at.is_(None))
        .order_by(AgentRun.created_at.desc())
        .limit(100)
    ).all()

    posts = []
    for r in runs:
        plan = r.plan or {}
        schedule = plan.get("schedule", {})
        meta = plan.get("metadata", {})
        posts.append({
            "run_id": str(r.id),
            "platform": meta.get("platform", "UNKNOWN"),
            "content_type": meta.get("content_type", "POST"),
            "scheduled_at": schedule.get("scheduled_at"),
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
        })

    if view == "daily":
        entries = SocialCalendar.get_daily_slots(posts)
    elif view == "weekly":
        entries = SocialCalendar.get_weekly_view(posts)
    else:
        entries = SocialCalendar.get_monthly_view(posts)

    return {"view": view, "entries": entries, "total_posts": len(posts)}


# ─── GET /platforms ───────────────────────────────────────────────────────────

@router.get("/platforms", response_model=List[SocialPlatformInfo])
def get_platforms() -> Any:
    """Return platform metadata for all 14 supported platforms."""
    results = []
    for platform_key, cfg in PLATFORM_CONFIGS.items():
        results.append(SocialPlatformInfo(
            platform=platform_key,
            char_limit=cfg.get("char_limit", 2200),
            hashtag_limit=cfg.get("hashtag_limit", 10),
            tone=cfg.get("tone", "professional"),
            emoji_friendly=cfg.get("emoji_friendly", False),
            supports_images=cfg.get("supports_images", True),
            supports_video=cfg.get("supports_video", False),
            supports_carousel=cfg.get("supports_carousel", False),
            supports_polls=cfg.get("supports_polls", False),
            best_practices=cfg.get("best_practices", []),
            image_ratio=cfg.get("image_ratio"),
        ))
    return results


# ─── GET /templates ───────────────────────────────────────────────────────────

@router.get("/templates")
def get_templates() -> Any:
    """Return social content type templates and prompting guides."""
    templates = []
    for ct in SocialContentType:
        templates.append({
            "id": ct.value,
            "name": ct.value.replace("_", " ").title(),
            "content_type": ct.value,
            "description": _get_content_type_description(ct),
            "platforms": _get_suitable_platforms(ct),
            "example_prompt": f"Write a compelling {ct.value.replace('_', ' ').lower()} about our new product launch",
        })
    return templates


# ─── GET /analytics ───────────────────────────────────────────────────────────

@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    platform: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
) -> Any:
    """Return social analytics summary derived from AgentRun records."""
    session = _resolve_social_session(db, membership.organization_id, membership.user_id)
    runs = db.scalars(
        select(AgentRun)
        .where(AgentRun.session_id == session.id, AgentRun.deleted_at.is_(None))
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    ).all()

    filtered = []
    content_types = {}
    for r in runs:
        plan = r.plan or {}
        meta = plan.get("metadata", {})
        run_platform = meta.get("platform", "")
        if platform and run_platform.upper() != platform.upper():
            continue
        ct = meta.get("content_type", "POST")
        content_types[ct] = content_types.get(ct, 0) + 1
        filtered.append({
            "run_id": str(r.id),
            "platform": run_platform,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "latency_ms": r.latency_ms,
            "tokens": r.total_tokens,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })

    avg_tokens = sum(r.get("tokens", 0) for r in filtered) / max(len(filtered), 1)
    avg_latency = sum(r.get("latency_ms", 0) or 0 for r in filtered) / max(len(filtered), 1)
    top_content_types = sorted(content_types, key=content_types.get, reverse=True)[:5]

    return {
        "platform": platform,
        "total_posts": len(filtered),
        "avg_tokens": round(avg_tokens, 1),
        "avg_latency_ms": round(avg_latency, 1),
        "top_content_types": top_content_types,
        "recent_runs": filtered[:10],
    }


# ─── GET /queue ───────────────────────────────────────────────────────────────

@router.get("/queue")
def get_queue(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    status_filter: Optional[str] = Query(None, alias="status"),
) -> Any:
    """Return the social publishing queue (scheduled + draft posts)."""
    session = _resolve_social_session(db, membership.organization_id, membership.user_id)
    runs = db.scalars(
        select(AgentRun)
        .where(AgentRun.session_id == session.id, AgentRun.deleted_at.is_(None))
        .order_by(AgentRun.created_at.desc())
        .limit(100)
    ).all()

    queue = []
    draft_count = 0
    scheduled_count = 0

    for r in runs:
        plan = r.plan or {}
        meta = plan.get("metadata", {})
        schedule = plan.get("schedule", {})
        post_status = schedule.get("status", "DRAFT")

        if status_filter and post_status.upper() != status_filter.upper():
            continue

        output_preview = ""
        if r.agent_output:
            try:
                content_obj = json.loads(r.agent_output)
                output_preview = content_obj.get("raw_content", "")[:150]
            except Exception:
                output_preview = str(r.agent_output)[:150]

        if post_status == "DRAFT":
            draft_count += 1
        elif post_status == "SCHEDULED":
            scheduled_count += 1

        queue.append(SocialQueueItem(
            run_id=str(r.id),
            platform=meta.get("platform", "UNKNOWN"),
            content_type=meta.get("content_type", "POST"),
            status=post_status,
            scheduled_at=schedule.get("scheduled_at"),
            preview=output_preview,
        ))

    return {
        "queue": [q.model_dump() for q in queue],
        "total": len(queue),
        "draft_count": draft_count,
        "scheduled_count": scheduled_count,
    }


# ─── Private Helpers ──────────────────────────────────────────────────────────

def _get_content_type_description(ct: SocialContentType) -> str:
    descriptions = {
        SocialContentType.POST: "Standard social media post",
        SocialContentType.THREAD: "Multi-part threaded post for extended storytelling",
        SocialContentType.CAROUSEL: "Multi-slide visual carousel post",
        SocialContentType.STORY: "24-hour ephemeral story content",
        SocialContentType.REEL: "Short-form video reel with hook and CTA",
        SocialContentType.SHORT: "YouTube Shorts or TikTok-style vertical video",
        SocialContentType.ANNOUNCEMENT: "Official company or product announcement",
        SocialContentType.LAUNCH_POST: "Product or feature launch post",
        SocialContentType.CASE_STUDY: "Success story with measurable outcomes",
        SocialContentType.TESTIMONIAL: "Customer testimonial or review highlight",
        SocialContentType.POLL: "Interactive audience poll",
        SocialContentType.QUESTION: "Conversation starter question post",
        SocialContentType.MEME: "Humorous meme with brand-aligned tone",
        SocialContentType.EDUCATIONAL: "Educational or how-to content",
        SocialContentType.PRODUCT_UPDATE: "Product changelog or feature update",
        SocialContentType.HIRING_POST: "Talent acquisition and hiring post",
        SocialContentType.COMMUNITY_POST: "Community engagement and culture post",
        SocialContentType.NEWSLETTER_PROMO: "Newsletter sign-up promotion",
        SocialContentType.EVENT_PROMO: "Event or webinar promotion",
        SocialContentType.BLOG_PROMO: "Blog article promotion",
    }
    return descriptions.get(ct, ct.value.replace("_", " ").title())


def _get_suitable_platforms(ct: SocialContentType) -> List[str]:
    platform_map = {
        SocialContentType.THREAD: ["TWITTER", "THREADS"],
        SocialContentType.CAROUSEL: ["INSTAGRAM", "LINKEDIN", "FACEBOOK"],
        SocialContentType.STORY: ["INSTAGRAM", "FACEBOOK"],
        SocialContentType.REEL: ["INSTAGRAM", "FACEBOOK", "TIKTOK"],
        SocialContentType.SHORT: ["YOUTUBE_SHORTS", "TIKTOK"],
        SocialContentType.MEME: ["INSTAGRAM", "TWITTER", "FACEBOOK", "REDDIT"],
        SocialContentType.CASE_STUDY: ["LINKEDIN", "TWITTER", "MEDIUM"],
        SocialContentType.EDUCATIONAL: ["LINKEDIN", "INSTAGRAM", "YOUTUBE_COMMUNITY", "MEDIUM", "QUORA"],
        SocialContentType.POLL: ["TWITTER", "LINKEDIN", "FACEBOOK", "INSTAGRAM", "YOUTUBE_COMMUNITY"],
        SocialContentType.NEWSLETTER_PROMO: ["LINKEDIN", "TWITTER", "FACEBOOK"],
    }
    return platform_map.get(ct, [p.value for p in SocialPlatform])
