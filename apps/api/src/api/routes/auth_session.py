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

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.auth import AuditLog
from api.models.iam import UserSession
from api.models.user import User
from api.middleware.auth_enforcement import require_active_account

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


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _get_current_session_id(request: Request) -> Optional[UUID]:
    """
    Extract current session ID from request context.
    Assumes session ID is stored in request.state during authentication.
    """
    return getattr(request.state, "session_id", None)


def log_audit(db: Session, user_id: UUID, action: str, request: Request, metadata: dict = None):
    """Log audit event."""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata=metadata or {},
    )
    db.add(audit)
    db.commit()


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
        .order_by(UserSession.last_activity_at.desc())
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
            last_activity_at=s.last_activity_at,
            expires_at=s.expires_at,
            is_current=(s.id == current_session_id),
        )
        for s in sessions
    ]
    
    return SessionListResponse(
        sessions=session_responses,
        total_count=len(session_responses),
    )


@router.delete("/{session_id}", response_model=RevokeSessionResponse)
def revoke_session(
    session_id: UUID,
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RevokeSessionResponse:
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
            detail="Session not found or already revoked.",
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
    
    return RevokeSessionResponse(
        success=True,
        message="Session revoked successfully.",
        revoked_session_id=session_id,
    )


@router.delete("", response_model=RevokeSessionResponse)
def revoke_all_sessions(
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RevokeSessionResponse:
    """
    Revoke ALL sessions except the current one.
    
    Use case: "Sign out everywhere else" - security measure when user
    suspects unauthorized access.
    """
    current_session_id = _get_current_session_id(request)
    
    # Revoke all sessions except current
    now = datetime.now(timezone.utc)
    revoked_count = (
        db.query(UserSession)
        .filter(
            UserSession.user_id == current_user.id,
            UserSession.id != current_session_id,
            UserSession.is_revoked == False,
        )
        .update(
            {
                "is_revoked": True,
                "revoked_at": now,
            },
            synchronize_session=False,
        )
    )
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
    )


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
        last_activity_at=session.last_activity_at,
        expires_at=session.expires_at,
        is_current=(session.id == current_session_id),
    )
