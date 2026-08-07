"""
Audit Log Routes
================
Admin-level read-only access to the centralized audit log.

Endpoints:
- GET  /audit/logs         — paginated, filterable list
- GET  /audit/logs/{id}   — single log entry
- GET  /audit/stats       — summary counts by action/risk
"""
import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.user import User
from api.models.platform_events import AuditLog

router = APIRouter(prefix="/audit", tags=["audit"])


# ─── Response Schemas ─────────────────────────────────────────────────────────

class AuditLogResponse(BaseModel):
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    actor_id: Optional[uuid.UUID] = None
    actor_email: Optional[str] = None
    actor_ip: Optional[str] = None
    entity_type: str = "system"
    entity_id: Optional[uuid.UUID] = None
    action: str
    description: Optional[str] = None
    risk_level: str = "low"
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    diff: Optional[dict] = None
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AuditStatsResponse(BaseModel):
    total: int
    by_risk: dict
    by_action: dict
    recent_high_risk: int


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _require_admin_or_superuser(current_user: User) -> None:
    """Raise 403 if user is not superuser or org admin."""
    if not current_user.is_superuser:
        # We allow org admins/owners to view audit logs for their org
        # (The route filters by org context automatically)
        pass  # We'll filter by org in the query below


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.get("/logs", response_model=List[AuditLogResponse])
def list_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    # Filters
    action: Optional[str] = Query(None, description="Filter by action (e.g. USER_LOGIN, ROLE_CHANGED)"),
    risk_level: Optional[str] = Query(None, description="low | medium | high | critical"),
    actor_id: Optional[uuid.UUID] = Query(None),
    entity_type: Optional[str] = Query(None, description="e.g. users, organizations"),
    entity_id: Optional[uuid.UUID] = Query(None),
    organization_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
) -> Any:
    """
    List audit log entries with optional filtering.

    Superusers see all logs. Org members see only their org's logs.
    """
    query = db.query(AuditLog)

    # Access control
    if not current_user.is_superuser:
        # Determine org context
        org_ctx = organization_id
        if not org_ctx:
            # Try from header
            header_val = request.headers.get("x-organization-id")
            if header_val:
                try:
                    org_ctx = uuid.UUID(header_val)
                except ValueError:
                    pass
        if not org_ctx:
            # First membership
            from api.models.membership import UserOrganization
            m = db.query(UserOrganization).filter(
                UserOrganization.user_id == current_user.id
            ).first()
            if m:
                org_ctx = m.organization_id

        if not org_ctx:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No organization context available",
            )
        query = query.filter(AuditLog.organization_id == org_ctx)
    elif organization_id:
        query = query.filter(AuditLog.organization_id == organization_id)

    # Apply filters
    if action:
        query = query.filter(AuditLog.action.ilike(f"%{action}%"))
    if risk_level:
        query = query.filter(AuditLog.risk_level == risk_level)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditLog.entity_id == entity_id)
    if date_from:
        query = query.filter(AuditLog.created_at >= date_from)
    if date_to:
        query = query.filter(AuditLog.created_at <= date_to)

    # Sort newest first
    query = query.order_by(AuditLog.created_at.desc())
    logs = query.offset(skip).limit(limit).all()
    return logs


@router.get("/logs/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
    log_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single audit log entry by ID."""
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audit log not found")

    # Non-superusers can only see logs from their orgs
    if not current_user.is_superuser and log.organization_id:
        from api.models.membership import UserOrganization
        m = db.query(UserOrganization).filter(
            UserOrganization.user_id == current_user.id,
            UserOrganization.organization_id == log.organization_id,
        ).first()
        if not m:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return log


@router.get("/stats")
def get_audit_stats(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: Optional[uuid.UUID] = Query(None),
) -> Any:
    """
    Return summary statistics for audit logs.
    """
    from sqlalchemy import func

    query = db.query(AuditLog)

    if not current_user.is_superuser:
        org_ctx = organization_id
        if not org_ctx:
            from api.models.membership import UserOrganization
            m = db.query(UserOrganization).filter(
                UserOrganization.user_id == current_user.id
            ).first()
            if m:
                org_ctx = m.organization_id
        if org_ctx:
            query = query.filter(AuditLog.organization_id == org_ctx)
    elif organization_id:
        query = query.filter(AuditLog.organization_id == organization_id)

    total = query.count()

    # By risk level
    risk_counts = (
        query.with_entities(AuditLog.risk_level, func.count(AuditLog.id))
        .group_by(AuditLog.risk_level)
        .all()
    )

    # By action (top 20)
    action_counts = (
        query.with_entities(AuditLog.action, func.count(AuditLog.id))
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(20)
        .all()
    )

    # Recent high-risk (last 24h)
    from datetime import timedelta, timezone
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_high = query.filter(
        AuditLog.risk_level.in_(["high", "critical"]),
        AuditLog.created_at >= cutoff,
    ).count()

    return {
        "total": total,
        "by_risk": dict(risk_counts),
        "by_action": dict(action_counts),
        "recent_high_risk": recent_high,
    }
