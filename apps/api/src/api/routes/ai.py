import uuid
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.prompt import Prompt
from api.models.conversation import Conversation
from api.models.message import Message
from api.services.llm import LLMGateway
from api.services.prompt import PromptService
from api.services.knowledge import KnowledgeService
from api.schemas.ai import (
    PromptCreate,
    PromptResponse,
    PromptUpdate,
    ConversationCreate,
    ConversationResponse,
    MessageCreate,
    MessageResponse,
    KnowledgeUploadRequest,
    DocumentChunkResponse,
    KnowledgeDocumentResponse,
    QuerySimilarChunksRequest,
    PlaygroundRunRequest,
    PlaygroundRunResponse,
)

prompts_router = APIRouter(prefix="/ai/prompts", tags=["ai-prompts"])
conversations_router = APIRouter(prefix="/ai/conversations", tags=["ai-conversations"])

active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


# ==========================================
# PROMPT LIBRARY ENDPOINTS
# ==========================================


@prompts_router.post(
    "/", response_model=PromptResponse, status_code=status.HTTP_201_CREATED
)
def create_prompt(
    prompt_in: PromptCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    try:
        return PromptService.create_prompt_version(
            db=db, prompt_in=prompt_in, organization_id=membership.organization_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@prompts_router.post(
    "/{name}/update", response_model=PromptResponse
)
def update_prompt(
    name: str,
    prompt_in: PromptUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    try:
        return PromptService.update_prompt_version(
            db=db, name=name, prompt_in=prompt_in, organization_id=membership.organization_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@prompts_router.get("/", response_model=List[PromptResponse])
def list_prompts(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.list_latest_prompts(
        db=db, organization_id=membership.organization_id
    )


@prompts_router.get("/{name}", response_model=PromptResponse)
def get_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prompt = PromptService.get_latest_prompt(
        db=db, name=name, organization_id=membership.organization_id
    )
    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Prompt template not found"
        )
    return prompt


@prompts_router.get("/{name}/history", response_model=List[PromptResponse])
def get_prompt_history(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return PromptService.get_prompt_history(
        db=db, name=name, organization_id=membership.organization_id
    )


@prompts_router.delete("/{name}", status_code=status.HTTP_204_NO_CONTENT)
def delete_prompt(
    name: str,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    PromptService.delete_prompt_family(
        db=db, name=name, organization_id=membership.organization_id
    )


@prompts_router.post("/test", response_model=PlaygroundRunResponse)
def test_prompt(
    test_in: PlaygroundRunRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # 1. Build messages
    messages = []
    if test_in.system_prompt:
        messages.append({"role": "system", "content": test_in.system_prompt})
    messages.append({"role": "user", "content": test_in.user_prompt})

    # 2. Call gateway
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    res = gateway.chat(
        db=db,
        messages=messages,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        model_name=test_in.model_name,
    )

    # 3. Log Token Usage to DB
    from api.models.ai_usage import AITokenUsage
    usage = AITokenUsage(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        provider=res.get("provider", "unknown"),
        model_name=res.get("model", test_in.model_name),
        prompt_tokens=res.get("prompt_tokens", 0),
        completion_tokens=res.get("completion_tokens", 0),
        total_tokens=res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
        cost_usd=res.get("cost_usd", 0.0),
        latency_ms=res.get("latency_ms", 0),
        status="success",
    )
    db.add(usage)
    db.commit()

    return {
        "output": res["content"],
        "provider": res.get("provider", "unknown"),
        "model": res.get("model", test_in.model_name),
        "tokens_used": res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
        "cost_usd": float(res.get("cost_usd", 0.0)),
        "latency_ms": res.get("latency_ms", 0),
    }


# ==========================================
# CONVERSATION HISTORY ENDPOINTS
# ==========================================


@conversations_router.post(
    "/", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED
)
def create_conversation(
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    conv = Conversation(
        title=conv_in.title,
        user_id=current_user.id,
        organization_id=membership.organization_id,
    )
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


@conversations_router.get("/", response_model=List[ConversationResponse])
def list_conversations(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    return (
        db.query(Conversation)
        .filter(
            Conversation.organization_id == membership.organization_id,
            Conversation.user_id == current_user.id,
        )
        .all()
    )


@conversations_router.delete(
    "/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_conversation(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    db.delete(conv)
    db.commit()


@conversations_router.patch(
    "/{conversation_id}", response_model=ConversationResponse
)
def rename_conversation(
    conversation_id: uuid.UUID,
    conv_in: ConversationCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    conv.title = conv_in.title
    db.commit()
    db.refresh(conv)
    return conv


@conversations_router.get(
    "/{conversation_id}/messages", response_model=List[MessageResponse]
)
def list_messages(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Ensure conversation belongs to current organization
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )


@conversations_router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
)
def post_message(
    conversation_id: uuid.UUID,
    msg_in: MessageCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # 1. Verify conversation session context
    conv = (
        db.query(Conversation)
        .filter(
            Conversation.id == conversation_id,
            Conversation.organization_id == membership.organization_id,
        )
        .first()
    )
    if not conv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation session not found",
        )

    # 2. Extract optional prompt instruction
    system_instruction = None
    if msg_in.prompt_id:
        prompt = (
            db.query(Prompt)
            .filter(
                Prompt.id == msg_in.prompt_id,
                Prompt.organization_id == membership.organization_id,
            )
            .first()
        )
        if not prompt:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Applied prompt template does not exist inside this organization.",
            )
        system_instruction = prompt.content
    elif msg_in.system_prompt:
        system_instruction = msg_in.system_prompt

    # 3. Log user message
    user_msg = Message(
        conversation_id=conversation_id,
        role="user",
        content=msg_in.content,
        model_used=msg_in.model_name,
    )
    db.add(user_msg)
    db.commit()

    # 4. Fetch session history to construct chat payload
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )

    messages_payload = []
    if system_instruction:
        messages_payload.append({"role": "system", "content": system_instruction})
    for h in history:
        messages_payload.append({"role": h.role, "content": h.content})

    # 5. Trigger AI Gateway 2.0 Orchestrator
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    res = gateway.chat(
        db=db,
        messages=messages_payload,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        rag_enabled=msg_in.rag_enabled,
        model_name=msg_in.model_name,
    )

    # 6. Log assistant response with full telemetry metrics
    assistant_msg = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=res["content"],
        model_used=res.get("model", msg_in.model_name),
        provider_used=res.get("provider"),
        latency_ms=res.get("latency_ms"),
        prompt_tokens=res.get("prompt_tokens"),
        completion_tokens=res.get("completion_tokens"),
        cost_usd=res.get("cost_usd"),
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return assistant_msg


knowledge_router = APIRouter(prefix="/ai/knowledge", tags=["ai-knowledge"])


@knowledge_router.post("/", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    doc_in: KnowledgeUploadRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return KnowledgeService.upload_document(
        db=db,
        doc_in=doc_in,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
    )


@knowledge_router.post("/query", response_model=List[DocumentChunkResponse])
def query_similar_chunks(
    query_in: QuerySimilarChunksRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return KnowledgeService.query_similar_chunks(
        db=db,
        query_text=query_in.query_text,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        limit=query_in.limit or 3,
    )


# ==========================================
# MODEL REGISTRY, ROUTING & USAGE ENDPOINTS
# ==========================================

from api.models.ai_registry import AIModelRegistry, AIRoutingRule
from api.models.ai_usage import AITokenUsage
from api.ai.registry.manager import ModelRegistryManager
from api.schemas.ai import (
    ModelRegistryResponse,
    ModelRegistryUpdate,
    RoutingRuleResponse,
    RoutingRuleCreate,
    RoutingRuleUpdate,
    TokenUsageResponse,
)
from sqlalchemy import select, delete
import random
import datetime
from datetime import timedelta
from decimal import Decimal

models_router = APIRouter(prefix="/ai/models", tags=["ai-models"])
routing_rules_router = APIRouter(prefix="/ai/routing-rules", tags=["ai-routing-rules"])
usage_router = APIRouter(prefix="/ai/usage", tags=["ai-usage"])


@models_router.get("/", response_model=List[ModelRegistryResponse])
def list_models(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Auto-seed standard models if registry is empty
    ModelRegistryManager.seed_default_models(db)
    models = db.scalars(
        select(AIModelRegistry)
        .where(
            (AIModelRegistry.organization_id == None) | 
            (AIModelRegistry.organization_id == membership.organization_id)
        )
        .order_by(AIModelRegistry.provider.asc(), AIModelRegistry.priority.desc())
    ).all()
    return models


@models_router.patch("/{model_id}", response_model=ModelRegistryResponse)
def update_model(
    model_id: uuid.UUID,
    model_in: ModelRegistryUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    model = db.scalars(
        select(AIModelRegistry)
        .where(
            AIModelRegistry.id == model_id,
            (AIModelRegistry.organization_id == None) |
            (AIModelRegistry.organization_id == membership.organization_id)
        )
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found in registry",
        )
    
    update_data = model_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(model, field, value)
        
    db.commit()
    db.refresh(model)
    return model


@routing_rules_router.get("/", response_model=List[RoutingRuleResponse])
def list_routing_rules(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Make sure default models are seeded so routing rules exist
    ModelRegistryManager.seed_default_models(db)
    rules = db.scalars(
        select(AIRoutingRule)
        .where(
            (AIRoutingRule.organization_id == None) |
            (AIRoutingRule.organization_id == membership.organization_id)
        )
    ).all()
    return rules


@routing_rules_router.post("/", response_model=RoutingRuleResponse, status_code=status.HTTP_201_CREATED)
def create_routing_rule(
    rule_in: RoutingRuleCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Verify model exists
    model = db.scalars(
        select(AIModelRegistry).where(AIModelRegistry.id == rule_in.model_registry_id)
    ).first()
    if not model:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target model registry ID does not exist"
        )
    
    rule = AIRoutingRule(
        request_type=rule_in.request_type,
        model_registry_id=rule_in.model_registry_id,
        is_active=rule_in.is_active,
        organization_id=membership.organization_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@routing_rules_router.patch("/{rule_id}", response_model=RoutingRuleResponse)
def update_routing_rule(
    rule_id: uuid.UUID,
    rule_in: RoutingRuleUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    rule = db.scalars(
        select(AIRoutingRule)
        .where(
            AIRoutingRule.id == rule_id,
            (AIRoutingRule.organization_id == None) |
            (AIRoutingRule.organization_id == membership.organization_id)
        )
    ).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )
    
    update_data = rule_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(rule, field, value)
        
    db.commit()
    db.refresh(rule)
    return rule


@routing_rules_router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_rule(
    rule_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    rule = db.scalars(
        select(AIRoutingRule)
        .where(
            AIRoutingRule.id == rule_id,
            (AIRoutingRule.organization_id == None) |
            (AIRoutingRule.organization_id == membership.organization_id)
        )
    ).first()
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Routing rule not found"
        )
    db.delete(rule)
    db.commit()


def seed_dummy_usages(db: Session, organization_id: uuid.UUID, user_id: uuid.UUID) -> None:
    # Check if there is any usage logged for this org
    existing = db.scalars(
        select(AITokenUsage).where(AITokenUsage.organization_id == organization_id)
    ).first()
    if existing:
        return
        
    # Generate mock logs over the last 14 days
    now = datetime.datetime.now(datetime.timezone.utc)
    models_sample = [
        {"provider": "openai", "model": "gpt-4o-mini", "in_cost": 0.00015, "out_cost": 0.0006},
        {"provider": "openai", "model": "gpt-4o", "in_cost": 0.005, "out_cost": 0.015},
        {"provider": "groq", "model": "llama3-70b-8192", "in_cost": 0.00059, "out_cost": 0.00079},
        {"provider": "groq", "model": "llama3-8b-8192", "in_cost": 0.00005, "out_cost": 0.0001},
        {"provider": "google", "model": "gemini-1.5-flash", "in_cost": 0.000075, "out_cost": 0.0003},
        {"provider": "anthropic", "model": "claude-3-5-sonnet-20240620", "in_cost": 0.003, "out_cost": 0.015},
    ]
    
    statuses = ["success"] * 90 + ["failure"] * 10
    error_messages = ["Rate limit exceeded", "Context window overflow", "Provider connection timed out", "Internal server error"]
    
    for i in range(120):
        # random date in last 14 days
        days_ago = random.randint(0, 13)
        hours_ago = random.randint(0, 23)
        mins_ago = random.randint(0, 59)
        created_time = now - datetime.timedelta(days=days_ago, hours=hours_ago, minutes=mins_ago)
        
        m = random.choice(models_sample)
        prompt_t = random.randint(100, 4000)
        compl_t = random.randint(50, 2000)
        cost = Decimal(prompt_t * m["in_cost"] / 1000 + compl_t * m["out_cost"] / 1000)
        latency = random.randint(80, 2500) if m["provider"] == "groq" else random.randint(400, 4000)
        
        status_val = random.choice(statuses)
        err = random.choice(error_messages) if status_val == "failure" else None
        
        usage = AITokenUsage(
            organization_id=organization_id,
            user_id=user_id,
            provider=m["provider"],
            model_name=m["model"],
            prompt_tokens=prompt_t,
            completion_tokens=compl_t,
            total_tokens=prompt_t + compl_t,
            cost_usd=cost,
            latency_ms=latency,
            status=status_val,
            error_message=err,
        )
        # Override the server default created_at
        usage.created_at = created_time
        db.add(usage)
        
    db.commit()


@usage_router.get("/", response_model=List[TokenUsageResponse])
def list_usage(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    # Seed mock usage data for better analytics display if empty
    seed_dummy_usages(db, membership.organization_id, membership.user_id)
    
    usages = db.scalars(
        select(AITokenUsage)
        .where(AITokenUsage.organization_id == membership.organization_id)
        .order_by(AITokenUsage.created_at.desc())
    ).all()
    return usages


# ==========================================
# ENTERPRISE AI GATEWAY & PLATFORM ROUTERS
# ==========================================

from api.models.ai_platform import (
    AIProvider, AIModel, AIProviderKey, AIProviderHealth,
    AIRequest, AIUsage, AICost, AIPlaygroundSession, AIPlaygroundMessage,
    AIOrgLimit
)
from api.core.encryption import encrypt_key, decrypt_key
from pydantic import BaseModel
from api.schemas.ai import (
    ProviderResponse, ProviderCreate, ProviderUpdate, ProviderHealthResponse,
    PlaygroundChatRequest, CompareRequest, CompareResponse, CompareResponseElement,
    RouterSettingsResponse, RouterSettingsUpdate
)
import httpx
import os
import time
import json
from fastapi.responses import StreamingResponse

providers_router = APIRouter(prefix="/ai/providers", tags=["ai-providers"])
playground_router = APIRouter(prefix="/ai/playground", tags=["ai-playground"])
compare_router = APIRouter(prefix="/ai/compare", tags=["ai-compare"])
router_settings_router = APIRouter(prefix="/ai/router", tags=["ai-router"])
analytics_router = APIRouter(prefix="/ai/analytics", tags=["ai-analytics"])


def sync_providers_and_models(db: Session) -> None:
    """
    Synchronize dynamic list of providers and models in PostgreSQL.
    """
    provider_names = ["groq", "openai", "anthropic", "google", "openrouter"]
    providers = {}
    for name in provider_names:
        prov = db.query(AIProvider).filter(AIProvider.name == name).first()
        if not prov:
            prov = AIProvider(name=name, is_active=True, priority=1)
            db.add(prov)
            db.flush()
        providers[name] = prov
    db.commit()

    groq_api_key = os.getenv("GROQ_API_KEY")
    groq_models = []
    if groq_api_key:
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.get(
                    "https://api.groq.com/openai/v1/models",
                    headers={"Authorization": f"Bearer {groq_api_key}"}
                )
                if res.status_code == 200:
                    data = res.json()
                    for m in data.get("data", []):
                        m_id = m.get("id")
                        if m_id:
                            groq_models.append(m_id)
        except Exception:
            pass

    if not groq_models:
        groq_models = [
            "openai/gpt-oss-120b",
            "llama-3.3-70b-versatile",
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma2-9b-it",
        ]

    # Seed defaults inside ModelRegistry
    ModelRegistryManager.seed_default_models(db)

    registry_models = {model.model_name: model for model in db.query(AIModelRegistry).all()}
    for model_name in groq_models:
        if model_name in registry_models:
            continue
        registry_models[model_name] = AIModelRegistry(
            provider="groq",
            model_name=model_name,
            context_window=131072 if "70b" in model_name or model_name == "openai/gpt-oss-120b" else 8192,
            supports_streaming=True,
            supports_json=True,
            input_token_price=Decimal("0.0000"),
            output_token_price=Decimal("0.0000"),
            latency=Decimal("0.20"),
            priority=8,
            is_healthy=True,
        )
        db.add(registry_models[model_name])

    db.commit()

    # Sync default registry entries to new ai_models table
    for reg_model in db.query(AIModelRegistry).all():
        m = db.query(AIModel).filter(AIModel.model_name == reg_model.model_name).first()
        if not m:
            prov = providers.get(reg_model.provider)
            if prov:
                m = AIModel(
                    provider_id=prov.id,
                    model_name=reg_model.model_name,
                    context_window=reg_model.context_window,
                    input_token_price=reg_model.input_token_price,
                    output_token_price=reg_model.output_token_price,
                    supports_streaming=reg_model.supports_streaming,
                    supports_vision=reg_model.supports_vision,
                    supports_tools=reg_model.supports_tool_calling,
                    supports_json=reg_model.supports_json,
                    is_active=True
                )
                db.add(m)
    db.commit()


@providers_router.get("/", response_model=List[ProviderResponse])
def get_providers(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sync_providers_and_models(db)
    return db.query(AIProvider).order_by(AIProvider.priority.desc()).all()


@providers_router.post("/", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
def create_provider(
    prov_in: ProviderCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    existing = db.query(AIProvider).filter(AIProvider.name == prov_in.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Provider name already exists.")
    prov = AIProvider(name=prov_in.name, is_active=prov_in.is_active, priority=prov_in.priority or 1)
    db.add(prov)
    db.commit()
    db.refresh(prov)
    return prov


@providers_router.put("/{id}", response_model=ProviderResponse)
def update_provider(
    id: uuid.UUID,
    prov_in: ProviderUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    
    update_data = prov_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(prov, field, value)
    db.commit()
    db.refresh(prov)
    return prov


@providers_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_provider(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    db.delete(prov)
    db.commit()


@providers_router.get("/{id}/health", response_model=ProviderHealthResponse)
def check_provider_health(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
    
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    adapter = gateway._get_provider_adapter(db, prov.name, membership.organization_id)
    
    is_healthy = False
    start_time = time.perf_counter()
    err_msg = None
    if adapter:
        try:
            is_healthy = adapter.health()
        except Exception as e:
            err_msg = str(e)
    latency = int((time.perf_counter() - start_time) * 1000)

    health = AIProviderHealth(
        provider_id=prov.id,
        latency=latency,
        is_healthy=is_healthy,
        last_checked=datetime.datetime.utcnow(),
        error_message=err_msg
    )
    db.add(health)
    db.commit()

    return {
        "provider_name": prov.name,
        "is_healthy": is_healthy,
        "latency": latency,
        "last_checked": datetime.datetime.utcnow(),
        "error_message": err_msg
    }


# ==============================================================================
# SCHEMAS AND ENDPOINTS FOR KEYS, INCIDENTS, BUDGETS, AND LIMITS (PHASE 1)
# ==============================================================================

class ProviderKeyResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    provider_name: str
    is_active: bool
    masked_key: str
    created_at: datetime.datetime

    class Config:
        from_attributes = True

class ProviderKeyCreate(BaseModel):
    provider_id: uuid.UUID
    api_key: str
    is_active: Optional[bool] = True

class ProviderKeyRotate(BaseModel):
    api_key: str

class ProviderHealthLogResponse(BaseModel):
    id: uuid.UUID
    provider_id: uuid.UUID
    latency: int
    is_healthy: bool
    last_checked: datetime.datetime
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class OrgCapLimitResponse(BaseModel):
    organization_id: uuid.UUID
    credit_limit: float
    credit_used: float
    rpm_limit: int
    tpm_limit: int

    class Config:
        from_attributes = True

class AddCreditsRequest(BaseModel):
    amount: float

class UpdateLimitsRequest(BaseModel):
    rpm_limit: int
    tpm_limit: int
    credit_limit: Optional[float] = None


@providers_router.get("/keys/", response_model=List[ProviderKeyResponse])
def get_provider_keys(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    keys = db.query(AIProviderKey).filter(
        AIProviderKey.organization_id == membership.organization_id
    ).all()
    
    result = []
    for k in keys:
        plain_key = ""
        try:
            plain_key = decrypt_key(k.api_key)
        except Exception:
            pass
        
        masked = "sk-*****"
        if len(plain_key) > 10:
            masked = f"{plain_key[:7]}*****{plain_key[-4:]}"
            
        result.append({
            "id": k.id,
            "provider_id": k.provider_id,
            "provider_name": k.provider_rel.name if k.provider_rel else "unknown",
            "is_active": k.is_active,
            "masked_key": masked,
            "created_at": k.created_at,
        })
    return result

@providers_router.post("/keys/", response_model=ProviderKeyResponse)
def create_or_update_provider_key(
    key_in: ProviderKeyCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    prov = db.query(AIProvider).filter(AIProvider.id == key_in.provider_id).first()
    if not prov:
        raise HTTPException(status_code=404, detail="Provider not found.")
        
    existing = db.query(AIProviderKey).filter(
        AIProviderKey.provider_id == key_in.provider_id,
        AIProviderKey.organization_id == membership.organization_id
    ).first()
    
    encrypted = encrypt_key(key_in.api_key)
    
    if existing:
        existing.api_key = encrypted
        existing.is_active = key_in.is_active if key_in.is_active is not None else existing.is_active
        db.commit()
        db.refresh(existing)
        target = existing
    else:
        new_key = AIProviderKey(
            provider_id=key_in.provider_id,
            organization_id=membership.organization_id,
            api_key=encrypted,
            is_active=key_in.is_active if key_in.is_active is not None else True
        )
        db.add(new_key)
        db.commit()
        db.refresh(new_key)
        target = new_key
        
    plain_key = key_in.api_key
    masked = f"{plain_key[:7]}*****{plain_key[-4:]}" if len(plain_key) > 10 else "sk-*****"
    
    return {
        "id": target.id,
        "provider_id": target.provider_id,
        "provider_name": prov.name,
        "is_active": target.is_active,
        "masked_key": masked,
        "created_at": target.created_at,
    }

@providers_router.post("/keys/{key_id}/rotate", response_model=ProviderKeyResponse)
def rotate_provider_key(
    key_id: uuid.UUID,
    rotate_in: ProviderKeyRotate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    key_rec = db.query(AIProviderKey).filter(
        AIProviderKey.id == key_id,
        AIProviderKey.organization_id == membership.organization_id
    ).first()
    if not key_rec:
        raise HTTPException(status_code=404, detail="Provider key record not found.")
        
    encrypted = encrypt_key(rotate_in.api_key)
    key_rec.api_key = encrypted
    db.commit()
    db.refresh(key_rec)
    
    plain_key = rotate_in.api_key
    masked = f"{plain_key[:7]}*****{plain_key[-4:]}" if len(plain_key) > 10 else "sk-*****"
    
    return {
        "id": key_rec.id,
        "provider_id": key_rec.provider_id,
        "provider_name": key_rec.provider_rel.name if key_rec.provider_rel else "unknown",
        "is_active": key_rec.is_active,
        "masked_key": masked,
        "created_at": key_rec.created_at,
    }

@providers_router.get("/health-logs", response_model=List[ProviderHealthLogResponse])
def get_provider_health_logs(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    logs = db.query(AIProviderHealth).order_by(AIProviderHealth.last_checked.desc()).limit(100).all()
    return logs

@providers_router.get("/health/incidents")
def get_provider_incidents(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    failures = db.query(AIProviderHealth).filter(
        AIProviderHealth.is_healthy == False
    ).order_by(AIProviderHealth.last_checked.desc()).limit(30).all()
    
    incidents = []
    for f in failures:
        newer_check = db.query(AIProviderHealth).filter(
            AIProviderHealth.provider_id == f.provider_id,
            AIProviderHealth.last_checked > f.last_checked
        ).order_by(AIProviderHealth.last_checked.asc()).first()
        
        resolved = newer_check.is_healthy if newer_check else False
        
        incidents.append({
            "id": str(f.id),
            "provider": f.provider_rel.name if f.provider_rel else "unknown",
            "timestamp": f.last_checked.isoformat(),
            "type": "Outage" if "timeout" in (f.error_message or "").lower() else "API Error",
            "message": f.error_message or "Connectivity failure.",
            "resolved": resolved,
        })
    return incidents

@providers_router.post("/health/incidents/{id}/resolve")
def resolve_health_incident(
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    log_rec = db.query(AIProviderHealth).filter(AIProviderHealth.id == id).first()
    if not log_rec:
        raise HTTPException(status_code=404, detail="Incident record not found.")
    
    log_rec.is_healthy = True
    db.commit()
    return {"success": True}

@providers_router.get("/limits/orgs", response_model=List[OrgCapLimitResponse])
def list_orgs_limits(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    limits = db.query(AIOrgLimit).all()
    return limits

@providers_router.get("/limits/current", response_model=OrgCapLimitResponse)
def get_current_org_limit(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    limit = db.query(AIOrgLimit).filter(
        AIOrgLimit.organization_id == membership.organization_id
    ).first()
    
    if not limit:
        limit = AIOrgLimit(
            organization_id=membership.organization_id,
            credit_limit=100.00,
            credit_used=0.000000,
            rpm_limit=60,
            tpm_limit=50000
        )
        db.add(limit)
        db.commit()
        db.refresh(limit)
        
    return limit

@providers_router.post("/limits/{org_id}/credits", response_model=OrgCapLimitResponse)
def add_credits_to_org(
    org_id: uuid.UUID,
    req: AddCreditsRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    limit = db.query(AIOrgLimit).filter(AIOrgLimit.organization_id == org_id).first()
    if not limit:
        limit = AIOrgLimit(
            organization_id=org_id,
            credit_limit=req.amount,
            credit_used=0.000000,
            rpm_limit=60,
            tpm_limit=50000
        )
        db.add(limit)
    else:
        limit.credit_limit = float(Decimal(str(limit.credit_limit)) + Decimal(str(req.amount)))
        
    db.commit()
    db.refresh(limit)
    return limit

@providers_router.post("/limits/{org_id}/limits", response_model=OrgCapLimitResponse)
def update_org_limits(
    org_id: uuid.UUID,
    req: UpdateLimitsRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    if membership.role not in [UserRole.OWNER, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Insufficient privileges.")
        
    limit = db.query(AIOrgLimit).filter(AIOrgLimit.organization_id == org_id).first()
    if not limit:
        limit = AIOrgLimit(
            organization_id=org_id,
            credit_limit=req.credit_limit or 100.00,
            credit_used=0.000000,
            rpm_limit=req.rpm_limit,
            tpm_limit=req.tpm_limit
        )
        db.add(limit)
    else:
        limit.rpm_limit = req.rpm_limit
        limit.tpm_limit = req.tpm_limit
        if req.credit_limit is not None:
            limit.credit_limit = req.credit_limit
            
    db.commit()
    db.refresh(limit)
    return limit


@models_router.post("/sync")
def sync_models_endpoint(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sync_providers_and_models(db)
    return {"success": True, "message": "Successfully synchronized AI models."}


@models_router.put("/{id}", response_model=ModelRegistryResponse)
def put_model_details(
    id: uuid.UUID,
    is_favorite: Optional[bool] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    m = db.query(AIModel).filter(AIModel.id == id).first()
    if not m:
        reg_model = db.query(AIModelRegistry).filter(AIModelRegistry.id == id).first()
        if reg_model:
            if is_active is not None:
                reg_model.is_healthy = is_active
            db.commit()
            db.refresh(reg_model)
            return reg_model
        raise HTTPException(status_code=404, detail="Model not found.")
    
    if is_favorite is not None:
        m.is_favorite = is_favorite
    if is_active is not None:
        m.is_active = is_active
    db.commit()
    db.refresh(m)
    return m


@playground_router.post("/chat")
def playground_chat(
    req: PlaygroundChatRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    messages = list(req.messages)
    if req.system_prompt:
        messages.insert(0, {"role": "system", "content": req.system_prompt})
        
    res = gateway.chat(
        db=db,
        messages=messages,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        temperature=req.temperature,
        model_name=req.model_name
    )
    
    session = AIPlaygroundSession(
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        name=f"Chat via {req.model_name}",
        provider=res.get("provider", "unknown"),
        model=req.model_name,
        temperature=req.temperature,
        system_prompt=req.system_prompt
    )
    db.add(session)
    db.flush()
    
    for msg in req.messages:
        db.add(AIPlaygroundMessage(session_id=session.id, role=msg["role"], content=msg["content"]))
    db.add(AIPlaygroundMessage(session_id=session.id, role="assistant", content=res["content"]))
    db.commit()
    
    return {
        "output": res["content"],
        "provider": res.get("provider", "unknown"),
        "model": req.model_name,
        "tokens_used": res.get("prompt_tokens", 0) + res.get("completion_tokens", 0),
        "cost_usd": float(res.get("cost_usd", 0.0)),
        "latency_ms": res.get("latency_ms", 0),
    }


@playground_router.post("/stream")
def playground_stream(
    req: PlaygroundChatRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    messages = list(req.messages)
    if req.system_prompt:
        messages.insert(0, {"role": "system", "content": req.system_prompt})
        
    def sse_generator():
        try:
            chunks = gateway.stream(
                db=db,
                messages=messages,
                organization_id=membership.organization_id,
                user_id=membership.user_id,
                temperature=req.temperature,
                model_name=req.model_name
            )
            for chunk in chunks:
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
            
    return StreamingResponse(sse_generator(), media_type="text/event-stream")


@playground_router.get("/history")
def get_playground_history(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    sessions = (
        db.query(AIPlaygroundSession)
        .filter(AIPlaygroundSession.organization_id == membership.organization_id)
        .order_by(AIPlaygroundSession.created_at.desc())
        .limit(20)
        .all()
    )
    res = []
    for s in sessions:
        msgs = db.query(AIPlaygroundMessage).filter(AIPlaygroundMessage.session_id == s.id).order_by(AIPlaygroundMessage.created_at.asc()).all()
        res.append({
            "id": s.id,
            "name": s.name,
            "provider": s.provider,
            "model": s.model,
            "temperature": float(s.temperature),
            "system_prompt": s.system_prompt,
            "created_at": s.created_at,
            "messages": [{"role": m.role, "content": m.content} for m in msgs]
        })
    return res


@router_settings_router.get("/", response_model=RouterSettingsResponse)
def get_router_settings(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return {
        "routing_mode": "cheapest",
        "fallback_provider": "groq",
        "is_active": True
    }


@router_settings_router.put("/", response_model=RouterSettingsResponse)
def update_router_settings(
    settings_in: RouterSettingsUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return {
        "routing_mode": settings_in.routing_mode or "cheapest",
        "fallback_provider": settings_in.fallback_provider or "groq",
        "is_active": settings_in.is_active if settings_in.is_active is not None else True
    }


@compare_router.post("/", response_model=CompareResponse)
def compare_models(
    req: CompareRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    from api.ai.gateway.coordinator import AIGateway
    gateway = AIGateway()
    
    results = []
    for model_name in req.model_names:
        messages = [{"role": "user", "content": req.prompt}]
        if req.system_prompt:
            messages.insert(0, {"role": "system", "content": req.system_prompt})
            
        try:
            res = gateway.chat(
                db=db,
                messages=messages,
                organization_id=membership.organization_id,
                user_id=membership.user_id,
                model_name=model_name
            )
            results.append({
                "model_name": model_name,
                "provider": res.get("provider", "unknown"),
                "response": res["content"],
                "latency_ms": res.get("latency_ms", 0),
                "prompt_tokens": res.get("prompt_tokens", 0),
                "completion_tokens": res.get("completion_tokens", 0),
                "cost_usd": float(res.get("cost_usd", 0.0)),
                "status": "success"
            })
        except Exception as e:
            results.append({
                "model_name": model_name,
                "provider": "unknown",
                "response": "",
                "latency_ms": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0.0,
                "status": "failure",
                "error_message": str(e)
            })
            
    return {"results": results}


@analytics_router.get("/")
def get_analytics_dashboard(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    seed_dummy_usages(db, membership.organization_id, membership.user_id)
    
    usages = db.scalars(
        select(AITokenUsage)
        .where(AITokenUsage.organization_id == membership.organization_id)
        .order_by(AITokenUsage.created_at.desc())
        .limit(200)
    ).all()
    
    total_cost = sum(float(u.cost_usd or 0.0) for u in usages)
    total_tokens = sum(u.total_tokens or 0 for u in usages)
    success_rate = (len([u for u in usages if u.status == "success"]) / len(usages) * 100) if usages else 100.0
    avg_latency = (sum(u.latency_ms or 0 for u in usages) / len(usages)) if usages else 0
    
    return {
        "kpis": {
            "total_requests": len(usages),
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "success_rate": round(success_rate, 2),
            "avg_latency": round(avg_latency, 2)
        },
        "usages": [
            {
                "id": u.id,
                "provider": u.provider,
                "model_name": u.model_name,
                "prompt_tokens": u.prompt_tokens,
                "completion_tokens": u.completion_tokens,
                "total_tokens": u.total_tokens,
                "cost_usd": float(u.cost_usd or 0.0),
                "latency_ms": u.latency_ms,
                "status": u.status,
                "created_at": u.created_at
            }
            for u in usages
        ]
    }


