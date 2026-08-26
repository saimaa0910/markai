import uuid
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select, delete
from pydantic import BaseModel
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.security import AISecurityPolicyRule, AISecurityEvent, AIScanLog, AIQuotaUsage

logger = logging.getLogger("api.routes.security")
router = APIRouter(prefix="/ai/security", tags=["ai-security"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])

class PolicyRuleCreate(BaseModel):
    name: str
    scope: str = "global"
    request_type: str = "*"
    allowed_providers: Optional[List[str]] = None
    allowed_models: Optional[List[str]] = None
    daily_token_limit: int = 0
    daily_request_limit: int = 0
    monthly_token_limit: int = 0
    monthly_request_limit: int = 0
    daily_budget_usd: float = 0.0
    monthly_budget_usd: float = 0.0
    moderation_actions: Optional[Dict[str, str]] = None
    pii_masking_policy: str = "redact"
    is_active: bool = True
    priority: int = 0

class PolicyRuleUpdate(BaseModel):
    name: Optional[str] = None
    scope: Optional[str] = None
    request_type: Optional[str] = None
    allowed_providers: Optional[List[str]] = None
    allowed_models: Optional[List[str]] = None
    daily_token_limit: Optional[int] = None
    daily_request_limit: Optional[int] = None
    monthly_token_limit: Optional[int] = None
    monthly_request_limit: Optional[int] = None
    daily_budget_usd: Optional[float] = None
    monthly_budget_usd: Optional[float] = None
    moderation_actions: Optional[Dict[str, str]] = None
    pii_masking_policy: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None

# Response schemas
class SecurityPolicyResponse(BaseModel):
    id: uuid.UUID
    name: str
    scope: str
    request_type: str
    allowed_providers: Optional[List[str]] = None
    allowed_models: Optional[List[str]] = None
    daily_token_limit: int
    daily_request_limit: int
    monthly_token_limit: int
    monthly_request_limit: int
    daily_budget_usd: float
    monthly_budget_usd: float
    moderation_actions: Optional[Dict[str, str]] = None
    pii_masking_policy: str
    is_active: bool
    priority: int
    organization_id: Optional[uuid.UUID] = None

    class Config:
        from_attributes = True

class SecurityEventResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    event_type: str
    severity: str
    trigger_source: str
    details: Optional[str] = None
    action_taken: str
    created_at: Any

    class Config:
        from_attributes = True

class ScanLogResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    prompt_length: int
    prompt_complexity: int
    risk_score: float
    pii_detected: bool
    secrets_detected: bool
    injection_risk: float
    classification: str
    created_at: Any

    class Config:
        from_attributes = True

class QuotaUsageResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    daily_tokens: int
    monthly_tokens: int
    daily_requests: int
    monthly_requests: int
    daily_spend: float
    monthly_spend: float
    last_reset_date: Any

    class Config:
        from_attributes = True


@router.get("/policies", response_model=List[SecurityPolicyResponse])
def get_security_policies(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    policies = db.scalars(
        select(AISecurityPolicyRule)
        .where(
            (AISecurityPolicyRule.organization_id == None) |
            (AISecurityPolicyRule.organization_id == membership.organization_id)
        )
    ).all()
    if not policies:
        from api.ai.security.pipeline import AISecurityPipeline
        pipeline = AISecurityPipeline()
        pipeline._get_active_policy(db, membership.organization_id)
        policies = db.scalars(
            select(AISecurityPolicyRule)
            .where(
                (AISecurityPolicyRule.organization_id == None) |
                (AISecurityPolicyRule.organization_id == membership.organization_id)
            )
        ).all()
    return policies


@router.post("/policies", response_model=SecurityPolicyResponse, status_code=status.HTTP_201_CREATED)
def create_security_policy(  # Sprint 8.3.1
    req: PolicyRuleCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    policy = AISecurityPolicyRule(
        name=req.name,
        scope=req.scope,
        request_type=req.request_type,
        allowed_providers=req.allowed_providers,
        allowed_models=req.allowed_models,
        daily_token_limit=req.daily_token_limit,
        daily_request_limit=req.daily_request_limit,
        monthly_token_limit=req.monthly_token_limit,
        monthly_request_limit=req.monthly_request_limit,
        daily_budget_usd=req.daily_budget_usd,
        monthly_budget_usd=req.monthly_budget_usd,
        moderation_actions=req.moderation_actions,
        pii_masking_policy=req.pii_masking_policy,
        is_active=req.is_active,
        priority=req.priority,
        organization_id=membership.organization_id,
    )
    db.add(policy)
    db.commit()
    db.refresh(policy)
    return policy


@router.put("/policies/{id}", response_model=SecurityPolicyResponse)
def update_security_policy(  # Sprint 8.3.1
    id: uuid.UUID,
    req: PolicyRuleUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    policy = db.query(AISecurityPolicyRule).filter(
        AISecurityPolicyRule.id == id,
        AISecurityPolicyRule.organization_id == membership.organization_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Security policy rule not found.")
        
    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(policy, field, value)
        
    db.commit()
    db.refresh(policy)
    return policy


@router.delete("/policies/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_security_policy(  # Sprint 8.3.1
    id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> None:
    policy = db.query(AISecurityPolicyRule).filter(
        AISecurityPolicyRule.id == id,
        AISecurityPolicyRule.organization_id == membership.organization_id
    ).first()
    if not policy:
        raise HTTPException(status_code=404, detail="Security policy rule not found.")
        
    db.delete(policy)
    db.commit()


@router.get("/events", response_model=List[SecurityEventResponse])
def get_security_events(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    events = db.scalars(
        select(AISecurityEvent)
        .where(AISecurityEvent.organization_id == membership.organization_id)
        .order_by(AISecurityEvent.created_at.desc())
        .limit(100)
    ).all()
    return events


@router.get("/audit", response_model=List[ScanLogResponse])
def get_audit_scans(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    scans = db.scalars(
        select(AIScanLog)
        .where(AIScanLog.organization_id == membership.organization_id)
        .order_by(AIScanLog.created_at.desc())
        .limit(100)
    ).all()
    return scans


@router.get("/quotas", response_model=List[QuotaUsageResponse])
def get_quota_usages(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    quotas = db.scalars(
        select(AIQuotaUsage)
        .where(AIQuotaUsage.organization_id == membership.organization_id)
    ).all()
    return quotas


@router.get("/moderation")
def get_moderation_stats(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    events = db.scalars(
        select(AISecurityEvent)
        .where(
            AISecurityEvent.organization_id == membership.organization_id,
            AISecurityEvent.event_type == "moderation_event"
        )
    ).all()
    
    categories: Dict[str, int] = {}
    for ev in events:
        cat = ev.details.replace("Triggered category: ", "") if ev.details else "unknown"
        categories[cat] = categories.get(cat, 0) + 1
        
    return categories


@router.get("/pii")
def get_pii_leaks_stats(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    events = db.scalars(
        select(AISecurityEvent)
        .where(
            AISecurityEvent.organization_id == membership.organization_id,
            AISecurityEvent.event_type == "pii_leak"
        )
    ).all()
    return len(events)
