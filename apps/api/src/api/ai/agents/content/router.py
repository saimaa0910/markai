"""
Content Agent API Router — Sprint 7.2
======================================
API routes for generating content, streaming, editing/improving copy,
and calculating SEO scoring parameters.
"""
import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentType, AgentStatus
from api.repositories.agent import agent_definition_repo, agent_session_repo
from api.ai.agents.content.constants import ContentType, ImprovementType
from api.ai.agents.content.schemas import (
    ContentGenerateRequest, ContentStreamRequest,
    ContentImproveRequest, ContentResponse, ContentTemplateResponse,
    ContentSEOMetrics
)
from api.ai.agents.content.service import ContentAgentService
from api.ai.agents.content.agent import content_agent
from api.ai.agents.content.evaluation import ContentEvaluator
from api.ai.agents.content import prompts

router = APIRouter(prefix="/content", tags=["content-agent"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


def _resolve_content_session(db: Session, org_id: uuid.UUID, user_id: uuid.UUID) -> AgentSession:
    """Finds or creates a persistent session dedicated to the content agent."""
    # Look for an existing ACTIVE Content agent definition
    from sqlalchemy import select
    agent = db.scalars(
        select(AgentDefinition).where(
            AgentDefinition.organization_id == org_id,
            AgentDefinition.agent_type == AgentType.CONTENT,
            AgentDefinition.status == AgentStatus.ACTIVE,
        )
    ).first()

    if not agent:
        # Create default content agent
        agent = AgentDefinition(
            name="Content Agent Studio",
            description="Flagship Enterprise Content Generation Agent",
            agent_type=AgentType.CONTENT,
            status=AgentStatus.ACTIVE,
            allowed_tools=["knowledge_tool", "calculator_tool", "analytics_tool"],
            organization_id=org_id,
            memory_enabled=True,
        )
        db.add(agent)
        db.commit()
        db.refresh(agent)

    # Find or create a session
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
            title="Content Studio Session",
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    return session


@router.post("/generate", response_model=ContentResponse, status_code=status.HTTP_200_OK)
def generate_content(
    payload: ContentGenerateRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Generate content synchronously using guidelines, search, reflection, and SEO metrics."""
    session = _resolve_content_session(db, membership.organization_id, membership.user_id)
    
    result = ContentAgentService.generate_content(
        db=db,
        session=session,
        content_type=payload.content_type,
        prompt=payload.prompt,
        brand_voice_override=payload.brand_voice_override,
        forbidden_words=payload.forbidden_words,
        preferred_words=payload.preferred_words,
        knowledge_collections=payload.knowledge_collections,
        target_audience=payload.target_audience,
        keywords=payload.keywords,
        preferred_model=payload.preferred_model,
        temperature=payload.temperature or 0.7,
        run_reflection=payload.run_reflection,
        run_evaluation=payload.run_evaluation,
    )
    return result


@router.post("/stream")
def stream_generate_content(
    payload: ContentStreamRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> StreamingResponse:
    """Generate content yielding SSE (Server-Sent Events) live streaming chunks."""
    # Resolve session
    if payload.session_id:
        session = agent_session_repo.get_by_id_and_org(
            db=db, id=payload.session_id, organization_id=membership.organization_id
        )
        if not session:
            raise HTTPException(status_code=404, detail="Content session not found")
    else:
        session = _resolve_content_session(db, membership.organization_id, membership.user_id)

    def event_generator():
        yield from ContentAgentService.stream_generate_content(
            db=db,
            session=session,
            content_type=payload.content_type,
            prompt=payload.prompt,
            brand_voice_override=payload.brand_voice_override,
            forbidden_words=payload.forbidden_words,
            preferred_words=payload.preferred_words,
            knowledge_collections=payload.knowledge_collections,
            target_audience=payload.target_audience,
            keywords=payload.keywords,
            preferred_model=payload.preferred_model,
            temperature=payload.temperature or 0.7,
            run_reflection=payload.run_reflection,
            run_evaluation=payload.run_evaluation,
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/improve")
def improve_content(
    payload: ContentImproveRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Apply content adjustments (rewrite, expand, tone-conversion, translation)."""
    improved = content_agent.execute_improvement(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        content=payload.content,
        improvement_type=payload.improvement_type,
        target_tone=payload.target_tone,
        target_audience=payload.target_audience,
        target_language=payload.target_language,
        keywords=payload.keywords,
        preferred_model=payload.preferred_model,
        temperature=payload.temperature or 0.5,
    )
    return {"improved_content": improved}


@router.post("/rewrite")
def rewrite_content(
    content: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Convenience rewrite endpoint."""
    improved = content_agent.execute_improvement(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        content=content,
        improvement_type=ImprovementType.REWRITE,
    )
    return {"improved_content": improved}


@router.post("/summarize")
def summarize_content(
    content: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Convenience summary endpoint."""
    improved = content_agent.execute_improvement(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        content=content,
        improvement_type=ImprovementType.SUMMARIZE,
    )
    return {"improved_content": improved}


@router.post("/translate")
def translate_content(
    content: str,
    language: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Convenience translate endpoint."""
    improved = content_agent.execute_improvement(
        db=db,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        content=content,
        improvement_type=ImprovementType.TRANSLATE,
        target_language=language,
    )
    return {"improved_content": improved}


@router.post("/seo", response_model=ContentSEOMetrics)
def evaluate_seo(
    content: str,
    keywords: Optional[List[str]] = Query(None),
    title: Optional[str] = Query(None),
    meta_desc: Optional[str] = Query(None),
) -> Any:
    """Calculate and grade word count, keyword density, and heading hierarchy metrics locally."""
    return ContentEvaluator.evaluate_seo(
        content=content,
        keywords=keywords,
        title=title,
        meta_desc=meta_desc,
    )


@router.get("/templates", response_model=List[ContentTemplateResponse])
def get_templates() -> Any:
    """List details of all built-in prompts and required variables."""
    return prompts.list_templates()


@router.get("/history")
def get_history(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """List execution records of generated content items."""
    session = _resolve_content_session(db, membership.organization_id, membership.user_id)
    
    from api.models.agent import AgentRun
    from sqlalchemy import select
    
    runs = db.scalars(
        select(AgentRun)
        .where(
            AgentRun.session_id == session.id,
            AgentRun.deleted_at.is_(None),
        )
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    ).all()

    return [
        {
            "run_id": str(r.id),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "user_input": r.user_input,
            "latency_ms": r.latency_ms,
            "tokens": r.total_tokens,
            "output_preview": r.agent_output[:200] if r.agent_output else "",
        }
        for r in runs
    ]
