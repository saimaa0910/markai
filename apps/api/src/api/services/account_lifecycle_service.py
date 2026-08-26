"""
EAIMOS Account Lifecycle Service (Sprint 8.3.1 Phase 3)
========================================================
Advanced account management: data export, audit history, deactivation,
lockout management, and data portability for GDPR/compliance.
"""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, Optional, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.models.user import User
from api.models.iam import UserSession
from api.models.platform_events import AuditLog

logger = logging.getLogger("eaimos.iam.account_lifecycle")


class AccountStatus(str, Enum):
    """Account status enumeration."""
    ACTIVE = "active"
    DEACTIVATED = "deactivated"
    LOCKED = "locked"
    DELETED = "deleted"
    PENDING_DELETION = "pending_deletion"


class ExportFormat(str, Enum):
    """Data export format options."""
    JSON = "json"
    CSV = "csv"


def _iso(value) -> Optional[str]:
    return value.isoformat() if value else None


class AccountLifecycleService:
    """
    Advanced Account Lifecycle Management Service.

    Responsibilities:
    - Account data export (GDPR compliance)
    - Account audit history tracking
    - Account deactivation/reactivation
    - Account lockout management
    - Data portability
    """

    # ─── Account Deactivation ─────────────────────────────────────────────

    @staticmethod
    async def deactivate_account(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Temporarily deactivate an account."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.is_active = False
        user.deactivated_at = datetime.now(timezone.utc)
        user.deactivation_reason = reason

        # Revoke all active sessions
        sessions_result = await db.execute(
            select(UserSession).where(
                UserSession.user_id == user.id,
                UserSession.is_revoked == False,
            )
        )
        sessions = sessions_result.scalars().all()
        now = datetime.now(timezone.utc)
        for session in sessions:
            session.is_revoked = True
            session.is_active = False
            session.revoked_at = now
            session.revocation_reason = "Account deactivated"

        await db.commit()

        return {
            "success": True,
            "user_id": str(user.id),
            "deactivated_at": _iso(user.deactivated_at),
            "sessions_revoked": len(sessions),
            "message": "Account successfully deactivated",
        }

    @staticmethod
    async def reactivate_account(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reactivate a deactivated account."""
        query = select(User)
        if email:
            query = query.where(User.email == email)
        else:
            query = query.where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError("Account not found")

        user.is_active = True
        user.deactivated_at = None
        user.deactivation_reason = None
        await db.commit()

        return {
            "success": True,
            "user_id": str(user.id),
            "message": "Account successfully reactivated. Please log in.",
        }

    @staticmethod
    async def request_deletion(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Request account deletion with a 30-day grace period."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        now = datetime.now(timezone.utc)
        scheduled = now + timedelta(days=30)
        user.deletion_requested_at = now
        user.scheduled_deletion_at = scheduled
        user.deletion_reason = reason
        await db.commit()

        return {
            "success": True,
            "user_id": str(user.id),
            "deletion_requested_at": _iso(now),
            "scheduled_deletion_at": _iso(scheduled),
        }

    @staticmethod
    async def cancel_deletion(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
    ) -> Dict[str, Any]:
        """Cancel a scheduled deletion."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.deletion_requested_at = None
        user.scheduled_deletion_at = None
        user.deletion_reason = None
        await db.commit()

        return {"success": True, "user_id": str(user.id), "message": "Deletion canceled"}

    @staticmethod
    async def confirm_deletion(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
    ) -> Dict[str, Any]:
        """Confirm immediate deletion (marks deleted_at)."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.deleted_at = datetime.now(timezone.utc)
        user.is_active = False
        await db.commit()

        return {"success": True, "user_id": str(user.id), "message": "Account deleted"}

    @staticmethod
    async def unlock_account(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
    ) -> Dict[str, Any]:
        """Unlock a locked account."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.locked_until = None
        user.failed_login_count = 0
        user.failed_login_attempts = 0
        await db.commit()

        return {"success": True, "user_id": str(user.id), "message": "Account unlocked"}

    # ─── Data Export ──────────────────────────────────────────────────────

    @staticmethod
    async def export_user_data(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
    ) -> Dict[str, Any]:
        """Export all user account data for GDPR compliance."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        sessions_result = await db.execute(
            select(UserSession)
            .where(UserSession.user_id == user.id)
            .order_by(UserSession.created_at)
        )
        sessions = sessions_result.scalars().all()

        audit_result = await db.execute(
            select(AuditLog)
            .where(AuditLog.actor_id == user.id)
            .order_by(AuditLog.created_at.desc())
        )
        audit_logs = audit_result.scalars().all()

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
                "device_name": getattr(s, "device_name", None),
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
        await db.commit()

        return {
            "user": user_payload,
            "sessions": sessions_payload,
            "audit_logs": audit_payload,
        }

    # ─── Status & Privacy ─────────────────────────────────────────────────

    @staticmethod
    async def get_lifecycle_status(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
    ) -> Dict[str, Any]:
        """Get account lifecycle status."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        scheduled = user.scheduled_deletion_at
        if scheduled and scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)
        deletion_scheduled = (
            user.deletion_requested_at is not None
            and scheduled is not None
            and scheduled > datetime.now(timezone.utc)
        )

        # Phase 8: derive lock state from the canonical locked_until field so
        # is_locked never drifts from the login lockout logic.
        locked_until = user.locked_until
        if locked_until and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        is_locked = locked_until is not None and locked_until > datetime.now(timezone.utc)

        return {
            "user_id": str(user.id),
            "is_active": user.is_active,
            "is_locked": is_locked,
            "deletion_scheduled": bool(deletion_scheduled),
            "deletion_requested_at": _iso(user.deletion_requested_at),
            "scheduled_deletion_at": _iso(user.scheduled_deletion_at),
            "deactivated_at": _iso(user.deactivated_at),
            "deleted_at": _iso(user.deleted_at),
        }

    @staticmethod
    async def get_privacy_dashboard(
        db: AsyncSession,
        user_id: Union[uuid.UUID, str],
    ) -> Dict[str, Any]:
        """Get privacy dashboard overview."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise ValueError(f"User {user_id} not found")

        data_summary = {
            "email": user.email,
            "full_name": user.full_name,
            "is_verified": user.is_verified,
            "mfa_enabled": user.mfa_enabled,
            "export_count": user.export_count or 0,
        }

        deletion_status = {
            "is_deleted": user.deleted_at is not None,
            "deleted_at": _iso(user.deleted_at),
            "deletion_requested_at": _iso(user.deletion_requested_at),
            "scheduled_deletion_at": _iso(user.scheduled_deletion_at),
        }

        return {
            "data_summary": data_summary,
            "export_history": [
                {"exported_at": _iso(user.last_export_at), "format": "json"}
            ]
            if user.last_export_at
            else [],
            "deletion_status": deletion_status,
        }
