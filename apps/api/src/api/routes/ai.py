import uuid
from typing import Any, List
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

