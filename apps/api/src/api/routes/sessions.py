"""
EAIMOS Session Management Routes
==================================
REST API for authenticated session lifecycle management.
Allows users to view, revoke, and audit their active sessions.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.auth import RefreshToken
from api.models.iam import UserSession
from api.models.user import User

router = APIRouter(prefix="/sessions", tags=["sessions"])


# ─── Schemas ─────────────────────────────────────────────────────────────────

class SessionResponse(BaseModel):
    id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    expires_at: str
    last_active_at: str
    created_at: str
    is_revoked: bool
    is_current: bool = False

    model_config = ConfigDict(from_attributes=True)

class RevokeSessionRequest(BaseModel):
    reason: Optional[str] = "user_logout"


# ─── List Sessions ────────────────────────────────────────────────────────────

@router.get("/", response_model=List[SessionResponse])
def list_sessions(  # Sprint 8.3.1
    include_revoked: bool = False,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """List all sessions for the current user."""
    query = db.query(UserSession).filter(UserSession.user_id == current_user.id)
    if not include_revoked:
        query = query.filter(UserSession.is_revoked == False)
    sessions = query.order_by(UserSession.last_active_at.desc()).all()

    # Determine current session from token
    current_session_id = _get_current_session_id(request)

    return [
        SessionResponse(
            id=str(s.id),
            ip_address=s.ip_address,
            user_agent=s.user_agent,
            country_code=s.country_code,
            city=s.city,
            expires_at=s.expires_at.isoformat() if s.expires_at else "",
            last_active_at=s.last_active_at.isoformat() if s.last_active_at else "",
            created_at=s.created_at.isoformat() if s.created_at else "",
            is_revoked=s.is_revoked,
            is_current=(str(s.id) == current_session_id),
        )
        for s in sessions
    ]


# ─── Get Session ──────────────────────────────────────────────────────────────

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(  # Sprint 8.3.1
    session_id: uuid.UUID,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Get a specific session by ID (must belong to current user)."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    current_session_id = _get_current_session_id(request)
    return SessionResponse(
        id=str(session.id),
        ip_address=session.ip_address,
        user_agent=session.user_agent,
        country_code=session.country_code,
        city=session.city,
        expires_at=session.expires_at.isoformat() if session.expires_at else "",
        last_active_at=session.last_active_at.isoformat() if session.last_active_at else "",
        created_at=session.created_at.isoformat() if session.created_at else "",
        is_revoked=session.is_revoked,
        is_current=(str(session.id) == current_session_id),
    )


# ─── Revoke Single Session ────────────────────────────────────────────────────

@router.delete("/{session_id}", status_code=status.HTTP_200_OK)
def revoke_session(  # Sprint 8.3.1
    session_id: uuid.UUID,
    body: RevokeSessionRequest = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Revoke a specific session (must belong to current user)."""
    session = db.query(UserSession).filter(
        UserSession.id == session_id,
        UserSession.user_id == current_user.id,
    ).first()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    if session.is_revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Session is already revoked")

    now = datetime.now(timezone.utc)
    session.is_revoked = True
    session.revoked_at = now
    session.revocation_reason = (body.reason if body else None) or "user_revoked"

    # Revoke associated refresh tokens
    db.query(RefreshToken).filter(
        RefreshToken.session_id == session_id,
        RefreshToken.is_revoked == False,
    ).update({RefreshToken.is_revoked: True})

    db.commit()
    return {"success": True, "message": "Session revoked successfully"}


# ─── Revoke All Sessions ──────────────────────────────────────────────────────

@router.delete("/", status_code=status.HTTP_200_OK)
def revoke_all_sessions(  # Sprint 8.3.1
    keep_current: bool = True,
    request: Request = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Revoke all sessions for the current user. Optionally keep the current session."""
    now = datetime.now(timezone.utc)
    current_session_id = _get_current_session_id(request) if keep_current else None

    query = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
    )
    sessions = query.all()

    revoked_count = 0
    for s in sessions:
        if keep_current and current_session_id and str(s.id) == current_session_id:
            continue
        s.is_revoked = True
        s.revoked_at = now
        s.revocation_reason = "logout_all_devices"
        # Revoke associated refresh tokens
        db.query(RefreshToken).filter(
            RefreshToken.session_id == s.id,
            RefreshToken.is_revoked == False,
        ).update({RefreshToken.is_revoked: True})
        revoked_count += 1

    db.commit()
    return {
        "success": True,
        "message": f"Revoked {revoked_count} session(s)",
        "revoked_count": revoked_count,
    }


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_current_session_id(request: Optional[Request]) -> Optional[str]:
    """Extract the current session ID from the JWT jti claim."""
    if not request:
        return None
    from api.core.security import ALGORITHM
    from api.core.config import settings
    from jose import jwt, JWTError
    try:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            return payload.get("jti")
    except (JWTError, Exception):
        pass
    return None
