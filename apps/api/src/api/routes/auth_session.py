"""
Sprint 8.3.1 - Session Management Routes
=========================================
User-facing session management:
- List active sessions
- Revoke specific session
- Revoke all sessions (except current)
- View session details

Security Features:
- Session enumeration protection (only show user's own sessions)
- Current session protection (can't revoke current session via single revoke)
- Device fingerprinting
- IP tracking
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.auth import AuditLog
from api.models.iam import UserSession
from api.models.user import User
from api.middleware.auth_enforcement import require_active_account

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/sessions", tags=["sessions"])


# ──────────────────────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    """Single session details for user."""
    id: UUID
    device_name: Optional[str]
    device_type: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    location: Optional[str]
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    is_current: bool
    
    class Config:
        from_attributes = True


class SessionListResponse(BaseModel):
    """List of user sessions."""
    sessions: List[SessionResponse]
    total_count: int


class RevokeSessionRequest(BaseModel):
    """Request to revoke a specific session."""
    session_id: UUID


class RevokeSessionResponse(BaseModel):
    """Response after session revocation."""
    success: bool
    message: str
    revoked_session_id: Optional[UUID] = None
    revoked_count: Optional[int] = None


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _get_current_session_id(request: Request) -> Optional[UUID]:
    """
    Extract current session ID from the JWT (session_id claim, falling back to jti).
    """
    try:
        from jose import jwt, JWTError

        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            claim = payload.get("session_id") or payload.get("jti")
            if claim:
                return UUID(str(claim))
    except (JWTError, Exception):
        pass
    return getattr(request.state, "session_id", None)


def log_audit(db: Session, user_id: UUID, action: str, request: Request, metadata: dict = None, organization_id: Optional[uuid.UUID] = None, risk_level: str = "low"):
    """Persist an immutable audit log entry (Phase 21: org-attributed, best-effort)."""
    try:
        if organization_id is None:
            header_val = request.headers.get("x-organization-id") if request else None
            if header_val:
                try:
                    organization_id = uuid.UUID(header_val)
                except ValueError:
                    organization_id = None
        if organization_id is None:
            from api.models.membership import UserOrganization

            membership = (
                db.query(UserOrganization)
                .filter(
                    UserOrganization.user_id == user_id,
                    UserOrganization.deleted_at == None,
                )
                .first()
            )
            if membership:
                organization_id = membership.organization_id

        description = f"Action: {action}"
        if metadata:
            description += f" - {metadata}"

        audit = AuditLog(
            organization_id=organization_id,
            actor_id=user_id,
            action=action,
            actor_ip=request.client.host if request.client else None,
            actor_user_agent=request.headers.get("user-agent") if request else None,
            entity_type="users",
            entity_id=user_id,
            description=description[:255] if description else None,
            risk_level=risk_level,
        )
        db.add(audit)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.warning(f"Failed to write audit log for action={action!r}: {exc}")


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.get("", response_model=SessionListResponse)
def list_sessions(
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionListResponse:
    """
    List all active sessions for the current user.
    
    Returns sessions sorted by last_activity_at (most recent first).
    Marks the current session with is_current=True.
    """
    current_session_id = _get_current_session_id(request)
    
    # Query active sessions (not revoked, not expired)
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.is_revoked == False,
            UserSession.expires_at > now,
        )
        .order_by(UserSession.last_active_at.desc())
        .all()
    )
    
    session_responses = [
        SessionResponse(
            id=s.id,
            device_name=s.device_name,
            device_type=s.device_type,
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            location=s.location,
            created_at=s.created_at,
            last_activity_at=s.last_active_at,
            expires_at=s.expires_at,
            is_current=(current_session_id is not None and s.id == current_session_id),
        )
        for s in sessions
    ]
    
    # Ensure the current request's session is always represented and marked.
    if current_session_id is not None:
        if not any(r.id == current_session_id for r in session_responses):
            session_responses.append(
                SessionResponse(
                    id=current_session_id,
                    device_name=None,
                    device_type=None,
                    ip_address=None,
                    user_agent=None,
                    location=None,
                    created_at=now,
                    last_activity_at=now,
                    expires_at=now
                    + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                    is_current=True,
                )
            )
    
    return SessionListResponse(
        sessions=session_responses,
        total_count=len(session_responses),
    )


@router.delete("/all", response_model=RevokeSessionResponse)
def revoke_all_sessions(
    except_current: bool = False,
    request: Request = None,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RevokeSessionResponse:
    """
    Revoke ALL sessions, optionally keeping the current one.

    Use case: "Sign out everywhere else" - security measure when user
    suspects unauthorized access.
    """
    current_session_id = _get_current_session_id(request)
    
    now = datetime.now(timezone.utc)
    sessions = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.is_revoked == False,
        )
        .order_by(UserSession.last_active_at.desc())
        .all()
    )
    
    # Resolve which session to protect when except_current is requested.
    exclude_id = None
    if except_current:
        if current_session_id is not None and any(s.id == current_session_id for s in sessions):
            exclude_id = current_session_id
        elif sessions:
            # Token session isn't a DB row yet; keep the most recently active one.
            exclude_id = sessions[0].id
    
    revoked_count = 0
    for s in sessions:
        if exclude_id is not None and s.id == exclude_id:
            continue
        s.is_revoked = True
        s.revoked_at = now
        revoked_count += 1
    db.commit()
    
    # Audit log
    log_audit(
        db,
        current_user.id,
        "ALL_SESSIONS_REVOKED",
        request,
        {"revoked_count": revoked_count},
    )
    
    return RevokeSessionResponse(
        success=True,
        message=f"Successfully revoked {revoked_count} session(s).",
        revoked_count=revoked_count,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def revoke_session(
    session_id: UUID,
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """
    Revoke a specific session.

    Security:
    - Cannot revoke current session (use /auth/logout instead)
    - Can only revoke own sessions
    """
    current_session_id = _get_current_session_id(request)
    
    # Prevent revoking current session
    if session_id == current_session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke current session. Use /auth/logout instead.",
        )
    
    # Find session
    session = db.query(UserSession).filter(UserSession.id == session_id).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or already revoked.",
        )
    
    if session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only revoke your own sessions.",
        )
    
    # Revoke session
    session.is_revoked = True
    session.revoked_at = datetime.now(timezone.utc)
    db.commit()
    
    # Audit log
    log_audit(
        db,
        current_user.id,
        "SESSION_REVOKED",
        request,
        {"revoked_session_id": str(session_id)},
    )
    
    return None


@router.get("/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: UUID,
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> SessionResponse:
    """
    Get details for a specific session.
    
    Security: Can only view own sessions.
    """
    current_session_id = _get_current_session_id(request)
    
    session = (
        db.query(UserSession)
        .filter(
            UserSession.id == session_id,
            UserSession.user_id == current_user.id,
        )
        .first()
    )
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found.",
        )
    
    return SessionResponse(
        id=session.id,
        device_name=session.device_name,
        device_type=session.device_type,
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        location=session.location,
        created_at=session.created_at,
        last_activity_at=session.last_active_at,
        expires_at=session.expires_at,
        is_current=(session.id == current_session_id),
    )
