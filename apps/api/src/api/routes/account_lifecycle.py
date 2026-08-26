"""
EAIMOS Account Lifecycle API Routes (Sprint 8.3.1 Phase 3)
===========================================================
Advanced account management endpoints for data export, deactivation,
lockout management, and audit history.
"""

import csv
import io
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import get_current_user, get_current_admin_user, get_user_org_membership
from api.models.user import User
from api.models.iam import UserSession
from api.models.membership import UserOrganization
from api.models.platform_events import AuditLog

logger = logging.getLogger("eaimos.api.account_lifecycle")

router = APIRouter(prefix="/account/lifecycle", tags=["Account Lifecycle"])


# ─── Request Models ───────────────────────────────────────────────────────────


class DeactivateAccountRequest(BaseModel):
    """Request body for account deactivation."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deactivation")


class ReactivateAccountRequest(BaseModel):
    """Request body for account reactivation."""
    email: str


class RequestDeletionRequest(BaseModel):
    """Request body for account deletion request."""
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deletion")


def _iso(value) -> Optional[str]:
    return value.isoformat() if value else None


def _get_user_or_404(db: Session, user_id) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


# ─── Account Deactivation ─────────────────────────────────────────────────────


@router.post("/deactivate", status_code=status.HTTP_200_OK)
async def deactivate_account(
    body: DeactivateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Temporarily deactivate your account."""
    current_user.is_active = False
    current_user.deactivated_at = datetime.now(timezone.utc)
    current_user.deactivation_reason = body.reason

    now = datetime.now(timezone.utc)
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id, UserSession.is_revoked == False)
        .all()
    )
    for session in sessions:
        session.is_revoked = True
        session.is_active = False
        session.revoked_at = now
        session.revocation_reason = "Account deactivated"

    db.commit()
    return {
        "user_id": str(current_user.id),
        "message": "Account successfully deactivated",
        "deactivated_at": _iso(current_user.deactivated_at),
    }


@router.post("/reactivate", status_code=status.HTTP_200_OK)
async def reactivate_account(
    body: ReactivateAccountRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reactivate your account by email."""
    # Verify the email belongs to the current user
    user = db.query(User).filter(User.email == body.email, User.id == current_user.id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found or email does not match your account",
        )
    user.is_active = True
    user.deactivated_at = None
    user.deactivation_reason = None
    db.commit()
    return {"user_id": str(user.id), "message": "Account successfully reactivated. Please log in."}


# ─── Account Deletion ─────────────────────────────────────────────────────────


@router.post("/request-deletion", status_code=status.HTTP_200_OK)
async def request_deletion(
    body: RequestDeletionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request account deletion with a 30-day grace period."""
    now = datetime.now(timezone.utc)
    scheduled = now + timedelta(days=30)
    current_user.deletion_requested_at = now
    current_user.scheduled_deletion_at = scheduled
    current_user.deletion_reason = body.reason
    db.commit()
    return {
        "success": True,
        "user_id": str(current_user.id),
        "deletion_requested_at": _iso(now),
        "scheduled_deletion_at": _iso(scheduled),
    }


@router.post("/cancel-deletion", status_code=status.HTTP_200_OK)
async def cancel_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel a scheduled deletion."""
    current_user.deletion_requested_at = None
    current_user.scheduled_deletion_at = None
    current_user.deletion_reason = None
    db.commit()
    return {"success": True, "user_id": str(current_user.id), "message": "Deletion canceled"}


@router.post("/confirm-deletion", status_code=status.HTTP_200_OK)
async def confirm_deletion(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Confirm immediate deletion (marks the account as deleted)."""
    current_user.deleted_at = datetime.now(timezone.utc)
    current_user.is_active = False
    db.commit()
    return {"success": True, "user_id": str(current_user.id), "message": "Account deleted"}


# ─── Status ───────────────────────────────────────────────────────────────────


@router.get("/status", status_code=status.HTTP_200_OK)
async def get_lifecycle_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get account lifecycle status for the current user only."""
    scheduled = current_user.scheduled_deletion_at
    if scheduled and scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)
    deletion_scheduled = (
        current_user.deletion_requested_at is not None
        and scheduled is not None
        and scheduled > datetime.now(timezone.utc)
    )
    return {
        "user_id": str(current_user.id),
        "is_active": current_user.is_active,
        "is_locked": current_user.locked_until is not None and current_user.locked_until > datetime.now(timezone.utc),
        "deletion_scheduled": bool(deletion_scheduled),
        "deletion_requested_at": _iso(current_user.deletion_requested_at),
        "scheduled_deletion_at": _iso(current_user.scheduled_deletion_at),
        "deactivated_at": _iso(current_user.deactivated_at),
        "deleted_at": _iso(current_user.deleted_at),
    }


# ─── Data Export ──────────────────────────────────────────────────────────────


def _export_payload(db: Session, user: User) -> dict:
    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == user.id)
        .order_by(UserSession.created_at)
        .all()
    )
    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.actor_id == user.id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    user_payload = {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_verified": user.is_verified,
        "created_at": _iso(user.created_at),
        "last_login_at": _iso(user.last_login_at),
    }

    sessions_payload = [
        {
            "id": str(s.id),
            "created_at": _iso(s.created_at),
            "last_active_at": _iso(s.last_active_at),
            "expires_at": _iso(s.expires_at),
            "ip_address": s.ip_address,
            "user_agent": s.user_agent,
            "is_revoked": s.is_revoked,
            "revoked_at": _iso(s.revoked_at),
        }
        for s in sessions
    ]

    audit_payload = [
        {
            "id": str(a.id),
            "event_type": a.action,
            "created_at": _iso(a.created_at),
            "ip_address": a.actor_ip,
        }
        for a in audit_logs
    ]

    user.export_count = (user.export_count or 0) + 1
    user.last_export_at = datetime.now(timezone.utc)

    return {
        "user": user_payload,
        "sessions": sessions_payload,
        "audit_logs": audit_payload,
    }


@router.get("/data-export", status_code=status.HTTP_200_OK)
async def export_user_data(
    format: str = Query("json", description="Export format: json or csv"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    org_membership: UserOrganization = Depends(get_user_org_membership),
):
    """Export user account data in JSON or CSV format.
    
    Users can only export their own data. Admins can export any user's data.
    """
    # Check if current_user is admin or requesting own data
    target_user = current_user
    if org_membership.role.value not in ("OWNER", "ADMIN"):
        # Non-admin can only export their own data
        target_user = current_user
    # Admins can specify any user via org membership context
    # (additional admin check would be in the admin deactivate endpoint)
    
    if format not in ("json", "csv"):
        return Response(
            content='{"detail":"Format must be json or csv"}',
            media_type="application/json",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    payload = _export_payload(db, target_user)
    db.commit()

    if format == "json":
        import json as _json
        return Response(
            content=_json.dumps(payload, default=str),
            media_type="application/json",
        )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["user", "sessions", "audit_logs"])
    writer.writerow([
        payload["user"]["email"],
        len(payload["sessions"]),
        len(payload["audit_logs"]),
    ])
    return Response(content=output.getvalue(), media_type="text/csv")


# ─── Privacy Dashboard ────────────────────────────────────────────────────────


@router.get("/privacy-dashboard", status_code=status.HTTP_200_OK)
async def get_privacy_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get privacy dashboard overview."""
    data_summary = {
        "email": current_user.email,
        "full_name": current_user.full_name,
        "is_verified": current_user.is_verified,
        "mfa_enabled": current_user.mfa_enabled,
        "export_count": current_user.export_count or 0,
    }
    deletion_status = {
        "is_deleted": current_user.deleted_at is not None,
        "deleted_at": _iso(current_user.deleted_at),
        "deletion_requested_at": _iso(current_user.deletion_requested_at),
        "scheduled_deletion_at": _iso(current_user.scheduled_deletion_at),
    }
    return {
        "data_summary": data_summary,
        "export_history": [
            {"exported_at": _iso(current_user.last_export_at), "format": "json"}
        ]
        if current_user.last_export_at
        else [],
        "deletion_status": deletion_status,
    }


# ─── Admin Operations ─────────────────────────────────────────────────────────


@router.post("/admin/deactivate/{user_id}", status_code=status.HTTP_200_OK)
async def admin_deactivate_user(
    user_id: uuid.UUID,
    body: DeactivateAccountRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Admin: deactivate any user's account."""
    user = _get_user_or_404(db, user_id)
    user.is_active = False
    user.deactivated_at = datetime.now(timezone.utc)
    user.deactivation_reason = body.reason
    db.commit()
    return {"user_id": str(user.id), "message": "User account deactivated"}


@router.post("/admin/unlock/{user_id}", status_code=status.HTTP_200_OK)
async def admin_unlock_account(
    user_id: uuid.UUID,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db),
):
    """Admin: unlock a user's locked account."""
    user = _get_user_or_404(db, user_id)
    user.locked_until = None
    user.failed_login_count = 0
    user.failed_login_attempts = 0
    db.commit()
    return {"user_id": str(user.id), "message": "Account unlocked"}
