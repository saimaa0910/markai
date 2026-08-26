from pydantic import BaseModel
import uuid
from typing import Any, List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog, AgentStatus
from api.repositories.agent import (
    agent_definition_repo,
    agent_session_repo,
    agent_run_repo,
    agent_log_repo,
)
from api.schemas.agent import (
    AgentDefinitionCreate,
    AgentDefinitionUpdate,
    AgentDefinitionResponse,
    AgentSessionCreate,
    AgentSessionUpdate,
    AgentSessionResponse,
    AgentRunCreate,
    AgentRunResponse,
    AgentLogResponse,
    # Sprint 7.1
    AgentChatRequest,
    AgentStreamRequest,
    AgentEvaluationResponse,
    AgentToolInfo,
)
from api.schemas.common import PaginatedResponse
from api.services.agent_executor import AgentExecutorService

router = APIRouter(prefix="/agents", tags=["agents"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])

# Sprint 7.2 Content Agent Router
from api.ai.agents.content import content_agent_router
router.include_router(content_agent_router)

# Sprint 7.4 Image Agent Router
from api.ai.agents.image.router import router as image_agent_router
router.include_router(image_agent_router)

# Sprint 7.5 Social Media Agent Router
from api.ai.agents.social import social_agent_router
router.include_router(social_agent_router)


# --- AGENT DEFINITION ENDPOINTS ---

@router.post(
    "/definitions",
    response_model=AgentDefinitionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_definition(
    agent_in: AgentDefinitionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    obj_data = agent_in.model_dump()
    return agent_definition_repo.create(
        db=db,
        obj_in=obj_data,
        organization_id=membership.organization_id,
        created_by=str(membership.user_id),
    )


@router.get("/definitions", response_model=PaginatedResponse[AgentDefinitionResponse])
def list_agent_definitions(  # Sprint 8.3.1: Auth enforcement
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    skip = (page - 1) * page_size
    items = agent_definition_repo.list_by_org(
        db=db, organization_id=membership.organization_id, skip=skip, limit=page_size
    )
    total = agent_definition_repo.count_by_org(
        db=db, organization_id=membership.organization_id
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/definitions/{agent_id}", response_model=AgentDefinitionResponse)
def get_agent_definition(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent definition not found",
        )
    return agent


@router.patch("/definitions/{agent_id}", response_model=AgentDefinitionResponse)
def update_agent_definition(
    agent_id: uuid.UUID,
    agent_in: AgentDefinitionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent definition not found",
        )
    update_data = agent_in.model_dump(exclude_unset=True)
    return agent_definition_repo.update(
        db=db, db_obj=agent, obj_in=update_data, updated_by=str(membership.user_id)
    )


@router.delete("/definitions/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_definition(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent definition not found",
        )
    agent_definition_repo.soft_delete(
        db=db, db_obj=agent, deleted_by=str(membership.user_id)
    )


# --- AGENT SESSION ENDPOINTS ---

@router.post(
    "/sessions",
    response_model=AgentSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_agent_session(
    session_in: AgentSessionCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify agent exists
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=session_in.agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target agent definition does not exist in your organization",
        )

    db_session = AgentSession(
        agent_id=session_in.agent_id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        title=session_in.title,
        context=session_in.context,
    )
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


@router.get("/sessions", response_model=PaginatedResponse[AgentSessionResponse])
def list_agent_sessions(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    skip = (page - 1) * page_size
    items = agent_session_repo.list_by_user_and_org(
        db=db,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        skip=skip,
        limit=page_size,
    )
    # Count sessions
    total = (
        db.query(AgentSession)
        .filter(
            AgentSession.user_id == membership.user_id,
            AgentSession.organization_id == membership.organization_id,
            AgentSession.deleted_at.is_(None),
        )
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/sessions/{session_id}", response_model=AgentSessionResponse)
def get_agent_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )
    return session


@router.patch("/sessions/{session_id}", response_model=AgentSessionResponse)
def update_agent_session(
    session_id: uuid.UUID,
    session_in: AgentSessionUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )
    update_data = session_in.model_dump(exclude_unset=True)
    return agent_session_repo.update(
        db=db, db_obj=session, obj_in=update_data, updated_by=str(membership.user_id)
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_agent_session(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )
    agent_session_repo.soft_delete(
        db=db, db_obj=session, deleted_by=str(membership.user_id)
    )


# --- EXECUTION & LOG RUN ENDPOINTS ---

@router.post(
    "/sessions/{session_id}/run",
    response_model=AgentRunResponse,
    status_code=status.HTTP_201_CREATED,
)
def run_agent_run(
    session_id: uuid.UUID,
    run_in: AgentRunCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )

    if not session.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot execute in an inactive session",
        )

    # Trigger core agent execution engine
    run = AgentExecutorService.run_agent_session(
        db=db, session=session, user_input=run_in.user_input
    )
    return run


@router.get("/sessions/{session_id}/runs", response_model=PaginatedResponse[AgentRunResponse])
def list_agent_runs(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    # Verify session access first
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent session not found",
        )

    skip = (page - 1) * page_size
    items = agent_run_repo.list_by_session(
        db=db, session_id=session_id, skip=skip, limit=page_size
    )
    total = (
        db.query(AgentRun)
        .filter(AgentRun.session_id == session_id, AgentRun.deleted_at.is_(None))
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/runs/{run_id}/logs", response_model=List[AgentLogResponse])
def list_run_logs(
    run_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify run exists and is within organization
    run = db.query(AgentRun).filter(
        AgentRun.id == run_id,
        AgentRun.organization_id == membership.organization_id,
        AgentRun.deleted_at.is_(None),
    ).first()
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent run execution record not found",
        )

    return agent_log_repo.list_by_run(db=db, run_id=run_id)


# --- TEMPLATES & EXTENDED CRUD ENDPOINTS ---

@router.get("/templates", response_model=List[Dict[str, Any]])
def list_agent_templates() -> Any:
    """Return three built-in production templates."""
    return [
        {
            "name": "Content Agent",
            "description": "Generates high-converting marketing collateral, blogs, landing pages, emails, social posts, ads, brand voice alignment, and video scripts.",
            "agent_type": "CONTENT",
            "system_prompt": "You are the Viptant Content Agent. You specialize in creating high-quality, SEO-optimized, brand-aligned marketing collateral including blogs, landing pages, email copy, and social posts. Always maintain the organization's brand voice and tone guidelines.",
            "allowed_tools": ["knowledge_tool", "prompt_tool"],
            "preferred_model": "gemini-2.5-pro",
            "temperature": 0.7,
            "max_tokens": 1500,
            "memory_enabled": True,
            "max_memory_items": 20,
            "max_iterations": 10,
            "is_public": True,
            "avatar_color": "violet",
            "avatar": "sparkles",
            "welcome_message": "Hello! I am your Content Creator Agent. How can I help you write copy, generate blog drafts, or craft emails today?",
            "reasoning_mode": "standard",
            "execution_mode": "sequential"
        },
        {
            "name": "SEO Agent",
            "description": "Performs keyword research, SERP analysis, topic clustering, SEO audits, meta tag generation, and content optimization recommendations.",
            "agent_type": "SEO",
            "system_prompt": "You are the Viptant SEO Agent. Your goal is to maximize organic search visibility. Audit the user's content, perform search query research, identify SERP trends, compile topic clusters, and draft high-performance meta tags.",
            "allowed_tools": ["web_search_tool", "knowledge_tool"],
            "preferred_model": "gemini-2.5-flash",
            "temperature": 0.5,
            "max_tokens": 1500,
            "memory_enabled": True,
            "max_memory_items": 20,
            "max_iterations": 10,
            "is_public": True,
            "avatar_color": "blue",
            "avatar": "search",
            "welcome_message": "Hello! I am your SEO Agent. Let's research keywords, perform SERP analyses, or optimize your content metadata for search engines.",
            "reasoning_mode": "cot",
            "execution_mode": "sequential"
        },
        {
            "name": "Campaign Agent",
            "description": "Orchestrates end-to-end multi-channel marketing campaigns, design A/B testing, and campaign copy variations across channels.",
            "agent_type": "CAMPAIGN",
            "system_prompt": "You are the Viptant Campaign Agent. You analyze performance data, coordinate multichannels, design A/B tests, recommend budget allocations, and automate promotional messaging.",
            "allowed_tools": ["campaign_tool", "web_search_tool"],
            "preferred_model": "gemini-2.5-pro",
            "temperature": 0.6,
            "max_tokens": 1500,
            "memory_enabled": True,
            "max_memory_items": 20,
            "max_iterations": 10,
            "is_public": True,
            "avatar_color": "emerald",
            "avatar": "megaphone",
            "welcome_message": "Hello! I am your Campaign Agent. Let's orchestrate, plan, and analyze marketing campaigns or creative copy variations.",
            "reasoning_mode": "standard",
            "execution_mode": "sequential"
        },
        {
            "name": "Social Media Agent",
            "description": "Plans, generates, optimizes, schedules, and publishes content across 14 social media platforms.",
            "agent_type": "SOCIAL",
            "system_prompt": "You are the Viptant Social Media Agent. You specialize in generating platform-optimized posts, threads, stories, and community content. You orchestrate caption writing, image generation, hashtag selection, and calendar scheduling.",
            "allowed_tools": ["knowledge_tool", "image_generation_tool", "campaign_tool", "analytics_tool", "brand_tool", "web_search_tool", "email_tool", "calendar_tool"],
            "preferred_model": "gemini-2.5-flash",
            "temperature": 0.75,
            "max_tokens": 1500,
            "memory_enabled": True,
            "max_memory_items": 20,
            "max_iterations": 10,
            "is_public": True,
            "avatar_color": "sky",
            "avatar": "share",
            "welcome_message": "Hello! I am your Social Media Agent. I can help you write platform-optimized captions, generate post images, schedule content, or build threads for Twitter and LinkedIn.",
            "reasoning_mode": "standard",
            "execution_mode": "sequential"
        },
        {
            "name": "Image Generation Agent",
            "description": "Generates visual assets, product mockups, and marketing graphics with style presets and aspect ratio layouts.",
            "agent_type": "IMAGE",
            "system_prompt": "You are the Viptant Image Generation Agent. You help visual creators and design teams generate product graphics, marketing visual mockups, and banner images. You structure prompt compilations, style presets selection, aspect ratio sizes, and follow brand design guidelines.",
            "allowed_tools": ["image_generate_tool", "image_edit_tool", "image_upscale_tool", "brand_tool", "knowledge_tool"],
            "preferred_model": "gemini-2.5-flash",
            "temperature": 0.7,
            "max_tokens": 1500,
            "memory_enabled": True,
            "max_memory_items": 20,
            "max_iterations": 10,
            "is_public": True,
            "avatar_color": "rose",
            "avatar": "image",
            "welcome_message": "Hello! I am your Image Generation Agent. I can help you generate product images, marketing graphics, edit visuals, or upscale images.",
            "reasoning_mode": "standard",
            "execution_mode": "sequential"
        }
    ]


@router.patch("/definitions/{agent_id}/favorite", response_model=AgentDefinitionResponse)
def toggle_favorite_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    agent.is_favorite = not agent.is_favorite
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/definitions/{agent_id}/pin", response_model=AgentDefinitionResponse)
def toggle_pin_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    agent.is_pinned = not agent.is_pinned
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/definitions/{agent_id}/archive", response_model=AgentDefinitionResponse)
def archive_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    agent.status = AgentStatus.ARCHIVED
    db.commit()
    db.refresh(agent)
    return agent


@router.patch("/definitions/{agent_id}/restore", response_model=AgentDefinitionResponse)
def restore_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    agent.status = AgentStatus.ACTIVE
    db.commit()
    db.refresh(agent)
    return agent


@router.post("/definitions/{agent_id}/duplicate", response_model=AgentDefinitionResponse, status_code=status.HTTP_201_CREATED)
def duplicate_agent(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    
    dup = AgentDefinition(
        name=f"{agent.name} (Copy)",
        description=agent.description,
        agent_type=agent.agent_type,
        status=AgentStatus.ACTIVE,
        system_prompt=agent.system_prompt,
        prompt_template_name=agent.prompt_template_name,
        allowed_tools=agent.allowed_tools,
        preferred_provider=agent.preferred_provider,
        preferred_model=agent.preferred_model,
        temperature=agent.temperature,
        top_p=agent.top_p,
        max_tokens=agent.max_tokens,
        memory_enabled=agent.memory_enabled,
        max_memory_items=agent.max_memory_items,
        max_iterations=agent.max_iterations,
        reasoning_mode=agent.reasoning_mode,
        execution_mode=agent.execution_mode,
        avatar=agent.avatar,
        avatar_color=agent.avatar_color,
        welcome_message=agent.welcome_message,
        is_public=False,
        organization_id=membership.organization_id,
    )
    db.add(dup)
    db.commit()
    db.refresh(dup)
    return dup


@router.get("/definitions/{agent_id}/export")
def export_agent_definition(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
    
    return {
        "name": agent.name,
        "description": agent.description,
        "agent_type": agent.agent_type.value,
        "system_prompt": agent.system_prompt,
        "prompt_template_name": agent.prompt_template_name,
        "allowed_tools": agent.allowed_tools,
        "preferred_provider": agent.preferred_provider,
        "preferred_model": agent.preferred_model,
        "temperature": agent.temperature,
        "top_p": agent.top_p,
        "max_tokens": agent.max_tokens,
        "memory_enabled": agent.memory_enabled,
        "max_memory_items": agent.max_memory_items,
        "max_iterations": agent.max_iterations,
        "reasoning_mode": agent.reasoning_mode,
        "execution_mode": agent.execution_mode,
        "avatar": agent.avatar,
        "avatar_color": agent.avatar_color,
        "welcome_message": agent.welcome_message,
    }


@router.post("/definitions/import", response_model=AgentDefinitionResponse, status_code=status.HTTP_201_CREATED)
def import_agent_definition(
    payload: Dict[str, Any],
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    try:
        from api.models.agent import AgentType
        agent_type = AgentType(payload.get("agent_type", "CUSTOM"))
    except ValueError:
        agent_type = AgentType.CUSTOM
        
    agent = AgentDefinition(
        name=payload.get("name", "Imported Agent"),
        description=payload.get("description"),
        agent_type=agent_type,
        status=AgentStatus.ACTIVE,
        system_prompt=payload.get("system_prompt"),
        prompt_template_name=payload.get("prompt_template_name"),
        allowed_tools=payload.get("allowed_tools", []),
        preferred_provider=payload.get("preferred_provider"),
        preferred_model=payload.get("preferred_model"),
        temperature=payload.get("temperature", 0.7),
        top_p=payload.get("top_p"),
        max_tokens=payload.get("max_tokens"),
        memory_enabled=payload.get("memory_enabled", True),
        max_memory_items=payload.get("max_memory_items", 20),
        max_iterations=payload.get("max_iterations", 10),
        reasoning_mode=payload.get("reasoning_mode"),
        execution_mode=payload.get("execution_mode"),
        avatar=payload.get("avatar"),
        avatar_color=payload.get("avatar_color"),
        welcome_message=payload.get("welcome_message"),
        is_public=False,
        organization_id=membership.organization_id,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return agent


@router.get("/definitions/{agent_id}/analytics")
def get_agent_analytics(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")
        
    runs = db.query(AgentRun).join(AgentSession).filter(
        AgentSession.agent_id == agent_id,
        AgentSession.organization_id == membership.organization_id,
        AgentRun.deleted_at.is_(None)
    ).all()
    
    total_runs = len(runs)
    successful_runs = sum(1 for r in runs if r.status.value == "COMPLETED")
    failed_runs = sum(1 for r in runs if r.status.value == "FAILED")
    success_rate = (successful_runs / total_runs * 100.0) if total_runs > 0 else 100.0
    
    total_tokens = sum(r.total_tokens for r in runs)
    avg_latency = sum(r.latency_ms for r in runs if r.latency_ms is not None) / len([r for r in runs if r.latency_ms is not None]) if len([r for r in runs if r.latency_ms is not None]) > 0 else 0
    
    total_cost = total_tokens * 0.000015
    
    tool_counts = {}
    for r in runs:
        if r.tool_calls:
            for tc in r.tool_calls:
                name = tc.get("tool_name")
                if name:
                    tool_counts[name] = tool_counts.get(name, 0) + 1
                    
    return {
        "agent_id": str(agent_id),
        "total_executions": total_runs,
        "success_rate": round(success_rate, 2),
        "failed_executions": failed_runs,
        "total_tokens_consumed": total_tokens,
        "average_latency_ms": round(avg_latency, 2),
        "total_cost_usd": round(total_cost, 6),
        "tool_usage": tool_counts,
        "preferred_model": agent.preferred_model or "Gateway Default",
        "preferred_provider": agent.preferred_provider or "Gateway Default"
    }


# ─────────────────────────────────────────────────────────────────────────────
# SPRINT 7.1 — RUNTIME ENDPOINTS
# ─────────────────────────────────────────────────────────────────────────────


@router.post("/definitions/{agent_id}/chat", response_model=AgentRunResponse, status_code=status.HTTP_201_CREATED)
def agent_chat(
    agent_id: uuid.UUID,
    chat_in: AgentChatRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    Single-turn convenience endpoint: creates a new session and executes a run.
    Uses the full Agent Runtime (context builder + reflection + evaluation).
    """
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")

    # Create ephemeral session
    session = AgentSession(
        agent_id=agent_id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        title=chat_in.session_title or "Chat Session",
        context=None,
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    # Use full Agent Runtime (extends existing AgentExecutorService)
    from api.ai.runtime.agent_runtime import agent_runtime
    result = agent_runtime.execute(
        db=db,
        session=session,
        user_input=chat_in.user_input,
        run_reflection=chat_in.run_reflection if chat_in.run_reflection is not None else True,
        run_evaluation=chat_in.run_evaluation if chat_in.run_evaluation is not None else True,
    )
    return result.run


@router.post("/definitions/{agent_id}/stream")
def agent_stream(
    agent_id: uuid.UUID,
    stream_in: AgentStreamRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> StreamingResponse:
    """
    SSE streaming agent execution endpoint.
    Yields Server-Sent Events throughout the agent lifecycle.

    Event types: agent_start, context_ready, plan, tool_call, tool_result,
                 token, reflection, evaluation, done, error
    """
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")

    # Resolve or create session
    if stream_in.session_id:
        session = agent_session_repo.get_by_id_and_org(
            db=db, id=stream_in.session_id, organization_id=membership.organization_id
        )
        if not session:
            raise HTTPException(status_code=404, detail="Agent session not found")
        if not session.is_active:
            raise HTTPException(status_code=400, detail="Cannot stream on an inactive session")
    else:
        session = AgentSession(
            agent_id=agent_id,
            user_id=membership.user_id,
            organization_id=membership.organization_id,
            title=stream_in.session_title or "Stream Session",
            context=None,
        )
        db.add(session)
        db.commit()
        db.refresh(session)

    from api.ai.runtime.streaming_runtime import agent_streaming_runtime

    def event_generator():
        yield from agent_streaming_runtime.stream_run(
            db=db,
            session=session,
            user_input=stream_in.user_input,
            conversation_history=stream_in.conversation_history or [],
            run_reflection=stream_in.run_reflection if stream_in.run_reflection is not None else True,
            run_evaluation=stream_in.run_evaluation if stream_in.run_evaluation is not None else True,
        )

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/definitions/{agent_id}/evaluations", response_model=List[AgentEvaluationResponse])
def list_agent_evaluations(
    agent_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """List evaluation scores for all runs of an agent."""
    agent = agent_definition_repo.get_by_id_and_org(
        db=db, id=agent_id, organization_id=membership.organization_id
    )
    if not agent:
        raise HTTPException(status_code=404, detail="Agent definition not found")

    from api.models.agent import AgentEvaluation
    from sqlalchemy import select

    evaluations = db.scalars(
        select(AgentEvaluation)
        .join(AgentRun, AgentEvaluation.run_id == AgentRun.id)
        .join(AgentSession, AgentRun.session_id == AgentSession.id)
        .where(
            AgentSession.agent_id == agent_id,
            AgentEvaluation.organization_id == membership.organization_id,
            AgentEvaluation.deleted_at.is_(None),
        )
        .order_by(AgentEvaluation.created_at.desc())
        .limit(limit)
    ).all()

    return evaluations


@router.get("", response_model=List[Dict[str, Any]])
def discover_agents(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    Agent Discovery API.
    Returns registered agents' manifests, capabilities, health, models, and tools.
    """
    from api.ai.agents.base.registry import AgentRegistry
    AgentRegistry.initialize()
    agents = AgentRegistry.list()
    return [
        {
            "id": a.manifest.id,
            "name": a.manifest.name,
            "description": a.manifest.description,
            "version": a.manifest.version,
            "category": a.manifest.category,
            "tags": a.manifest.tags,
            "icon": a.manifest.icon,
            "color": a.manifest.color,
            "owner": a.manifest.owner,
            "visibility": a.manifest.visibility,
            "capabilities": a.manifest.capabilities,
            "supported_providers": a.manifest.supported_providers,
            "supported_models": a.manifest.supported_models,
            "supported_tools": a.manifest.supported_tools,
            "required_permissions": a.manifest.required_permissions,
            "default_prompt": a.manifest.default_prompt,
            "default_model": a.manifest.default_model,
            "default_temperature": a.manifest.default_temperature,
            "default_max_tokens": a.manifest.default_max_tokens,
            "memory_requirements": a.manifest.memory_requirements,
            "knowledge_requirements": a.manifest.knowledge_requirements,
            "streaming_support": a.manifest.streaming_support,
            "reflection_support": a.manifest.reflection_support,
            "evaluation_support": a.manifest.evaluation_support,
            "telemetry_support": a.manifest.telemetry_support,
            "status": a.manifest.metadata.status.value if hasattr(a.manifest.metadata.status, "value") else str(a.manifest.metadata.status),
            "health": "healthy",
            "metadata": {
                "icon": a.manifest.metadata.icon,
                "gradient": a.manifest.metadata.gradient,
                "accent_color": a.manifest.metadata.accent_color,
                "category": a.manifest.metadata.category,
                "description": a.manifest.metadata.description,
                "author": a.manifest.metadata.author,
                "version": a.manifest.metadata.version,
                "release_notes": a.manifest.metadata.release_notes,
            }
        }
        for a in agents
    ]


@router.get("/tools", response_model=List[AgentToolInfo])
def list_available_tools(
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """List all tools available in the Tool Registry."""
    from api.ai.tools.registry import ToolRegistry
    tools = ToolRegistry.list_tools()
    return [
        AgentToolInfo(
            name=t.name,
            description=t.description,
            parameters_schema=t.parameters_schema,
        )
        for t in tools
    ]


@router.get("/sessions/{session_id}/memory")
def get_session_memory(
    session_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    limit: int = Query(20, ge=1, le=100),
) -> Any:
    """Retrieve memory items for a specific agent session."""
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from api.services.memory_manager import MemoryManager
    memory_items = MemoryManager.read_memory(
        db=db,
        agent_id=session.agent_id,
        organization_id=session.organization_id,
        session_id=session_id,
        limit=limit,
    )
    return [
        {
            "id": str(m.id),
            "memory_key": m.memory_key,
            "memory_value": m.memory_value,
            "memory_type": m.memory_type.value,
            "importance": m.importance,
            "access_count": m.access_count,
        }
        for m in memory_items
    ]


@router.post("/sessions/{session_id}/memory", status_code=status.HTTP_201_CREATED)
def write_session_memory(
    session_id: uuid.UUID,
    key: str,
    value: str,
    importance: float = 0.5,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Write a memory item to a session."""
    session = agent_session_repo.get_by_id_and_org(
        db=db, id=session_id, organization_id=membership.organization_id
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    from api.services.memory_manager import MemoryManager
    memory = MemoryManager.write_memory(
        db=db,
        agent_id=session.agent_id,
        organization_id=session.organization_id,
        key=key,
        value=value,
        session_id=session_id,
        importance=importance,
    )
    return {
        "id": str(memory.id),
        "memory_key": memory.memory_key,
        "memory_value": memory.memory_value,
        "memory_type": memory.memory_type.value,
        "importance": memory.importance,
    }


class MarketingAgentExecuteRequest(BaseModel):
    agent_id: str
    user_input: str
    session_id: Optional[uuid.UUID] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


class MarketingAgentStreamRequest(BaseModel):
    agent_id: str
    user_input: str
    session_id: Optional[uuid.UUID] = None
    conversation_history: Optional[List[Dict[str, str]]] = None


@router.post("/execute", response_model=Dict[str, Any])
def execute_agent(
    request: MarketingAgentExecuteRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Execute any registered AI agent dynamically based on its configuration."""
    from api.services.marketing_agent_service import MarketingAgentService
    try:
        result = MarketingAgentService.execute_agent(
            db=db,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            agent_id=request.agent_id,
            user_input=request.user_input,
            session_id=request.session_id,
            conversation_history=request.conversation_history
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/generate")
def generate_agent_response(
    request: MarketingAgentExecuteRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Alias for /execute to keep simple generative client compatibilities."""
    from api.services.marketing_agent_service import MarketingAgentService
    try:
        return MarketingAgentService.execute_agent(
            db=db,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            agent_id=request.agent_id,
            user_input=request.user_input,
            session_id=request.session_id,
            conversation_history=request.conversation_history
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/stream")
def stream_agent(
    request: MarketingAgentStreamRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Stream execution logs and tokens for any registered AI agent."""
    from api.services.marketing_agent_service import MarketingAgentService
    from fastapi.responses import StreamingResponse
    try:
        generator = MarketingAgentService.stream_agent(
            db=db,
            organization_id=membership.organization_id,
            user_id=membership.user_id,
            agent_id=request.agent_id,
            user_input=request.user_input,
            session_id=request.session_id,
            conversation_history=request.conversation_history
        )
        return StreamingResponse(generator, media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/history")
def get_global_history(
    session_id: Optional[uuid.UUID] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Retrieve history elements across session run instances."""
    if session_id:
        return get_session_memory(session_id=session_id, db=db, membership=membership)
    return []


@router.get("/runs")
def get_runs_metrics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Get list of active run executions organization-wide."""
    from api.models.agent import AgentRun
    runs = db.query(AgentRun).filter(AgentRun.organization_id == membership.organization_id).limit(50).all()
    return [
        {
            "id": str(r.id),
            "status": r.status.value if hasattr(r.status, "value") else str(r.status),
            "tokens_used": r.tokens_used,
            "cost": r.cost,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in runs
    ]


@router.get("/metrics")
def get_cost_metrics(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """Retrieve cost aggregated statistics."""
    from api.models.agent import AgentRun
    from sqlalchemy import func
    stats = db.query(
        func.sum(func.coalesce(AgentRun.cost, 0.0)).label("total_cost"),
        func.sum(func.coalesce(AgentRun.tokens_used, 0)).label("total_tokens"),
        func.count(AgentRun.id).label("total_runs")
    ).filter(AgentRun.organization_id == membership.organization_id).first()
    return {
        "total_cost": stats.total_cost or 0.0,
        "total_tokens": stats.total_tokens or 0,
        "total_runs": stats.total_runs or 0
    }

