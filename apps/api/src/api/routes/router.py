import uuid
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from pydantic import BaseModel

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.router import AIRoutingPolicy, AIRoutingLog, AIFailoverEvent
from api.models.ai_registry import AIModelRegistry
from api.ai.router.engine import ModelRouter
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

logger = logging.getLogger("api.routes.router")
router = APIRouter(prefix="/ai/router", tags=["ai-router"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])

class PolicyRuleCreate(BaseModel):
    name: str
    scope: str = "global"
    scope_id: Optional[str] = None
    request_type: str = "*"
    routing_strategy: str = "balanced"
    priority: int = 0
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool = True

class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = None
    scope: Optional[str] = None
    scope_id: Optional[str] = None
    request_type: Optional[str] = None
    routing_strategy: Optional[str] = None
    priority: Optional[int] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class SimulationRequest(BaseModel):
    prompt: str
    request_type: str = "chat"
    strategy: Optional[str] = None
    task_type: Optional[str] = None
    environment: Optional[str] = "development"
    min_context_window: Optional[int] = None
    load_balancer: Optional[str] = "priority"

# Response Schemas
class RoutingPolicyResponse(BaseModel):
    id: uuid.UUID
    name: str
    scope: str
    scope_id: Optional[str] = None
    request_type: str
    routing_strategy: str
    priority: int
    conditions: Optional[Dict[str, Any]] = None
    is_active: bool
    organization_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class RoutingLogResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    request_type: str
    strategy_used: str
    selected_provider: str
    selected_model: str
    fallback_count: int
    retry_count: int
    latency_ms: int
    cost_usd: float
    prompt_tokens: int
    completion_tokens: int
    success: bool
    error_message: Optional[str] = None

    class Config:
        from_attributes = True

class FailoverEventResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    failed_provider: str
    failed_model: str
    fallback_provider: str
    fallback_model: str
    error_message: Optional[str] = None
    retry_attempts: int

    class Config:
        from_attributes = True


@router.get("/strategies")
def get_routing_strategies(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return [
        {"id": "cheapest", "name": "Cheapest", "description": "Prioritize lowest priced model based on token registry rates."},
        {"id": "fastest", "name": "Fastest", "description": "Prioritize model with lowest average round-trip latency."},
        {"id": "highest_quality", "name": "Highest Quality", "description": "Prioritize premium reasoning models with highest priority parameter ranks."},
        {"id": "balanced", "name": "Balanced", "description": "Compromise combining health indicators, latency scores, and price limits."},
        {"id": "reasoning", "name": "Reasoning Focus", "description": "Force routing to reasoning models (Claude 3.5, GPT-4)."},
        {"id": "coding", "name": "Coding Focus", "description": "Force routing to coding optimized models (GPT-OSS)."},
        {"id": "vision", "name": "Vision Focus", "description": "Filter models supporting image inputs (Gemini, GPT-4o)."},
    ]


@router.get("/rules", response_model=List[RoutingPolicyResponse])
def list_routing_policies(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    policies = db.scalars(
        select(AIRoutingPolicy)
        .where(
            (AIRoutingPolicy.organization_id == None) |
            (AIRoutingPolicy.organization_id == membership.organization_id)
        )
        .order_by(AIRoutingPolicy.priority.desc())
    ).all()
    return policies


@router.post("/rules", response_model=RoutingPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_routing_policy(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    req: PolicyRuleCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    policy = AIRoutingPolicy(
        name=req.name,
        scope=req.scope,
        scope_id=req.scope_id,
        request_type=req.request_type,
        routing_strategy=req.routing_strategy,
        priority=req.priority,
        conditions=req.conditions,
        is_active=req.is_active,
        organization_id=membership.organization_id,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.put("/rules/{id}", response_model=RoutingPolicyResponse)
def update_routing_policy(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    id: uuid.UUID,
    req: PolicyRuleUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    policy = db.query(AIRoutingPolicy).filter(
        AIRoutingPolicy.id == id,
        (AIRoutingPolicy.organization_id == None) |
        (AIRoutingPolicy.organization_id == membership.organization_id)
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Routing policy not found.")
        
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
        
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/rules/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_routing_policy(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> None:
    policy = db.query(AIRoutingPolicy).filter(
        AIRoutingPolicy.id == id,
        AIRoutingPolicy.organization_id == membership.organization_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Routing policy not found.")
        
    db.delete(policy)
    db.commit()


@router.post("/simulate")
def simulate_routing(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    req: SimulationRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    router_engine = ModelRouter()
    candidates = router_engine.route(
        db=db,
        request_type=req.request_type,
        organization_id=membership.organization_id,
        user_id=membership.user_id,
        strategy=req.strategy,
        task_type=req.task_type,
        min_context_window=req.min_context_window,
        environment=req.environment,
        load_balancer=req.load_balancer,
    )
    
    if not candidates:
        raise HTTPException(status_code=400, detail="No models matched the given simulation parameters.")
        
    selected = candidates[0]
    backups = [c.model_name for c in candidates[1:]]
    
    # Estimate latency and price from registry values
    est_latency = float(selected.latency)
    est_cost = (len(req.prompt.split()) * float(selected.input_token_price) + 200 * float(selected.output_token_price)) / 1000000.0
    
    reason = (
        f"Selected model '{selected.model_name}' via provider '{selected.provider}' "
        f"based on strategy configuration. "
    )
    if req.strategy:
        reason += f"Matched explicit strategy override '{req.strategy}'."
    else:
        reason += "Matched dynamic router load balancing criteria."
        
    return {
        "selected_provider": selected.provider,
        "selected_model": selected.model_name,
        "fallbacks": backups,
        "estimated_latency_sec": est_latency,
        "estimated_cost_usd": round(est_cost, 6),
        "reason": reason
    }


@router.get("/analytics")
def get_router_analytics(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    usages = db.scalars(
        select(AIRoutingLog)
        .where(AIRoutingLog.organization_id == membership.organization_id)
        .order_by(AIRoutingLog.created_at.desc())
        .limit(100)
    ).all()
    
    total_requests = len(usages)
    success_requests = len([u for u in usages if u.success])
    success_rate = (success_requests / total_requests * 100.0) if total_requests else 100.0
    
    total_cost = sum(float(u.cost_usd) for u in usages)
    avg_latency = (sum(u.latency_ms for u in usages) / total_requests) if total_requests else 0.0
    total_fallbacks = sum(u.fallback_count for u in usages)
    total_retries = sum(u.retry_count for u in usages)
    
    # Return KPI blocks
    return {
        "kpis": {
            "total_requests": total_requests,
            "success_rate": round(success_rate, 2),
            "total_cost_usd": round(total_cost, 6),
            "avg_latency_ms": round(avg_latency, 2),
            "fallback_count": total_fallbacks,
            "retry_count": total_retries,
        },
        "live_feed": [
            {
                "id": str(u.id),
                "request_type": u.request_type,
                "strategy": u.strategy_used,
                "provider": u.selected_provider,
                "model": u.selected_model,
                "latency_ms": u.latency_ms,
                "cost_usd": float(u.cost_usd),
                "success": u.success,
                "created_at": u.created_at.isoformat()
            }
            for u in usages
        ]
    }


@router.get("/failovers", response_model=List[FailoverEventResponse])
def get_failover_logs(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    failovers = db.scalars(
        select(AIFailoverEvent)
        .where(AIFailoverEvent.organization_id == membership.organization_id)
        .order_by(AIFailoverEvent.created_at.desc())
        .limit(50)
    ).all()
    return failovers


@router.get("/health")
def get_router_health(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    models = db.scalars(select(AIModelRegistry)).all()
    
    results = []
    for m in models:
        results.append({
            "model_name": m.model_name,
            "provider": m.provider,
            "is_healthy": m.is_healthy,
            "avg_latency_sec": float(m.latency),
        })
    return results
