"""
EAIMOS Account Lifecycle Service (Sprint 8.3.1 Phase 3)
========================================================
Advanced account management: data export, audit history, deactivation,
lockout management, and data portability for GDPR/compliance.
"""

import csv
import io
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from api.models.iam import User, UserSession
from api.repositories.iam_repository import UserRepository, UserSessionRepository
from api.services.base import (
    BusinessRuleViolation,
    NotFoundError,
    ServiceContext,
    ServiceResult,
    ValidationError,
)

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

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
    ) -> None:
        from api.services.base.dependency_provider import container
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache

    # ─── Account Data Export ──────────────────────────────────────────────

    async def export_account_data(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        export_format: ExportFormat = ExportFormat.JSON,
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Export all user account data for GDPR compliance.
        
        Returns:
        - User profile data
        - Session history
        - Login history
        - Activity logs
        - Preferences/settings
        
        Business Rules:
        - User can only export their own data (unless admin)
        - Export includes all PII and activity data
        - Export is timestamped and audit-logged
        """
        try:
            user_id = uuid.UUID(str(user_id))
            
            # Authorization: User can export their own data or admin can export any
            if str(ctx.get_user_id_uuid()) != str(user_id):
                if not ctx.has_permission("admin:users:export"):
                    return ServiceResult.fail(
                        error="Unauthorized: Cannot export other user's data",
                        error_code="UNAUTHORIZED",
                        status_code=403,
                    )

            async with self.uow_service:
                user_repo: UserRepository = self.uow_service.get_repository(UserRepository)
                session_repo: UserSessionRepository = self.uow_service.get_repository(
                    UserSessionRepository
                )

                # Get user data
                user = await user_repo.get_by_id(
                    session=self.uow_service.session,
                    id=user_id,
                )
                if not user:
                    return ServiceResult.fail(
                        error=f"User {user_id} not found",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                # Get all sessions
                sessions = await session_repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=user_id,
                )

                # Build export data
                export_data = {
                    "export_metadata": {
                        "exported_at": datetime.now(timezone.utc).isoformat(),
                        "export_format": export_format.value,
                        "user_id": str(user_id),
                        "export_version": "1.0",
                    },
                    "account_profile": {
                        "id": str(user.id),
                        "email": user.email,
                        "display_name": user.display_name,
                        "role": user.role,
                        "is_verified": user.is_verified,
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "updated_at": user.updated_at.isoformat() if user.updated_at else None,
                        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                        "organization_id": str(user.organization_id) if user.organization_id else None,
                    },
                    "account_status": {
                        "is_active": user.is_active,
                        "is_locked": user.is_locked,
                        "is_deleted": user.deleted_at is not None,
                        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
                        "failed_login_attempts": user.failed_login_attempts,
                        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                    },
                    "security_settings": {
                        "mfa_enabled": user.mfa_enabled,
                        "change_password_required": user.change_password_required if hasattr(user, 'change_password_required') else None,
                        "password_changed_at": user.password_changed_at.isoformat() if hasattr(user, 'password_changed_at') and user.password_changed_at else None,
                    },
                    "session_history": [
                        {
                            "id": str(session.id),
                            "created_at": session.created_at.isoformat() if session.created_at else None,
                            "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None,
                            "expires_at": session.expires_at.isoformat() if session.expires_at else None,
                            "ip_address": session.ip_address,
                            "user_agent": session.user_agent,
                            "device_name": getattr(session, 'device_name', None),
                            "device_type": getattr(session, 'device_type', None),
                            "location": getattr(session, 'location', None),
                            "is_revoked": session.is_revoked,
                            "revoked_at": session.revoked_at.isoformat() if session.revoked_at else None,
                        }
                        for session in sessions
                    ],
                    "privacy_notice": {
                        "data_retention": "This export contains all personal data associated with your account.",
                        "right_to_erasure": "You may request permanent deletion of your account and all associated data.",
                        "data_portability": "This export is provided in a structured, machine-readable format.",
                    },
                }

                # Format based on requested format
                if export_format == ExportFormat.JSON:
                    formatted_data = export_data
                elif export_format == ExportFormat.CSV:
                    formatted_data = self._convert_to_csv(export_data)
                else:
                    formatted_data = export_data

                logger.info(
                    f"Account data exported for user {user_id}",
                    extra={
                        "user_id": str(user_id),
                        "export_format": export_format.value,
                        "correlation_id": ctx.correlation_id,
                    },
                )

                return ServiceResult.ok(
                    data={
                        "export_data": formatted_data,
                        "format": export_format.value,
                        "total_sessions": len(sessions),
                    }
                )

        except Exception as exc:
            logger.error(f"export_account_data failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    def _convert_to_csv(self, export_data: Dict[str, Any]) -> str:
        """Convert export data to CSV format."""
        output = io.StringIO()
        
        # Profile section
        writer = csv.writer(output)
        writer.writerow(["Section", "Field", "Value"])
        
        for section_name, section_data in export_data.items():
            if section_name == "session_history":
                continue  # Handle separately
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    writer.writerow([section_name, key, str(value)])
        
        # Session history section
        writer.writerow([])
        writer.writerow(["Session History"])
        if export_data.get("session_history"):
            sessions = export_data["session_history"]
            if sessions:
                headers = list(sessions[0].keys())
                writer.writerow(headers)
                for session in sessions:
                    writer.writerow([session.get(h) for h in headers])
        
        return output.getvalue()

    # ─── Account Deactivation ─────────────────────────────────────────────

    async def deactivate_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        reason: Optional[str] = None,
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Temporarily deactivate an account.
        
        Deactivation vs Deletion:
        - Deactivation: Temporary, reversible, data retained
        - Deletion: Permanent (after grace period), data removed
        
        Business Rules:
        - Deactivated accounts cannot log in
        - All active sessions are revoked
        - Account can be reactivated at any time
        - User profile and data remain intact
        """
        try:
            user_id = uuid.UUID(str(user_id))

            async with self.uow_service:
                user_repo: UserRepository = self.uow_service.get_repository(UserRepository)
                session_repo: UserSessionRepository = self.uow_service.get_repository(
                    UserSessionRepository
                )

                user = await user_repo.get_by_id(
                    session=self.uow_service.session,
                    id=user_id,
                )
                if not user:
                    return ServiceResult.fail(
                        error=f"User {user_id} not found",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                if not user.is_active:
                    return ServiceResult.fail(
                        error="Account is already deactivated",
                        error_code="ALREADY_DEACTIVATED",
                        status_code=400,
                    )

                # Deactivate account
                user.is_active = False
                user.deactivated_at = datetime.now(timezone.utc)
                user.deactivation_reason = reason
                user.updated_at = datetime.now(timezone.utc)

                await user_repo.update(
                    session=self.uow_service.session,
                    db_obj=user,
                    obj_in={"is_active": False},
                )

                # Revoke all active sessions
                active_sessions = await session_repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=user_id,
                )
                for session in active_sessions:
                    if not session.is_revoked:
                        session.is_revoked = True
                        session.revoked_at = datetime.now(timezone.utc)
                        session.revocation_reason = "Account deactivated"
                        await self.uow_service.session.flush()

                logger.info(
                    f"Account deactivated: {user_id}",
                    extra={
                        "user_id": str(user_id),
                        "reason": reason,
                        "sessions_revoked": len(active_sessions),
                        "correlation_id": ctx.correlation_id,
                    },
                )

                return ServiceResult.ok(
                    data={
                        "user_id": str(user_id),
                        "deactivated_at": user.deactivated_at.isoformat(),
                        "sessions_revoked": len(active_sessions),
                        "message": "Account successfully deactivated",
                    }
                )

        except Exception as exc:
            logger.error(f"deactivate_account failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def reactivate_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Reactivate a temporarily deactivated account.
        
        Business Rules:
        - Only deactivated accounts can be reactivated
        - Deleted accounts cannot be reactivated (use restore instead)
        - User must re-authenticate after reactivation
        """
        try:
            user_id = uuid.UUID(str(user_id))

            async with self.uow_service:
                user_repo: UserRepository = self.uow_service.get_repository(UserRepository)

                user = await user_repo.get_by_id(
                    session=self.uow_service.session,
                    id=user_id,
                )
                if not user:
                    return ServiceResult.fail(
                        error=f"User {user_id} not found",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                if user.is_active:
                    return ServiceResult.fail(
                        error="Account is already active",
                        error_code="ALREADY_ACTIVE",
                        status_code=400,
                    )

                if user.deleted_at is not None:
                    return ServiceResult.fail(
                        error="Deleted accounts must be restored, not reactivated",
                        error_code="ACCOUNT_DELETED",
                        status_code=400,
                    )

                # Reactivate account
                user.is_active = True
                user.deactivated_at = None
                user.deactivation_reason = None
                user.updated_at = datetime.now(timezone.utc)

                await user_repo.update(
                    session=self.uow_service.session,
                    db_obj=user,
                    obj_in={"is_active": True},
                )

                logger.info(
                    f"Account reactivated: {user_id}",
                    extra={
                        "user_id": str(user_id),
                        "correlation_id": ctx.correlation_id,
                    },
                )

                return ServiceResult.ok(
                    data={
                        "user_id": str(user_id),
                        "reactivated_at": user.updated_at.isoformat(),
                        "message": "Account successfully reactivated. Please log in.",
                    }
                )

        except Exception as exc:
            logger.error(f"reactivate_account failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Account Lockout Management ───────────────────────────────────────

    async def unlock_account(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Manually unlock a locked account.
        
        Business Rules:
        - Admin or user themselves can unlock
        - Resets failed login attempt counter
        - Clears locked_until timestamp
        - Audit-logged for security
        """
        try:
            user_id = uuid.UUID(str(user_id))

            async with self.uow_service:
                user_repo: UserRepository = self.uow_service.get_repository(UserRepository)

                user = await user_repo.get_by_id(
                    session=self.uow_service.session,
                    id=user_id,
                )
                if not user:
                    return ServiceResult.fail(
                        error=f"User {user_id} not found",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                if not user.is_locked:
                    return ServiceResult.fail(
                        error="Account is not locked",
                        error_code="NOT_LOCKED",
                        status_code=400,
                    )

                # Unlock account
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
                user.updated_at = datetime.now(timezone.utc)

                await user_repo.update(
                    session=self.uow_service.session,
                    db_obj=user,
                    obj_in={"is_locked": False, "failed_login_attempts": 0},
                )

                logger.info(
                    f"Account unlocked: {user_id}",
                    extra={
                        "user_id": str(user_id),
                        "unlocked_by": ctx.get_user_id_str(),
                        "correlation_id": ctx.correlation_id,
                    },
                )

                return ServiceResult.ok(
                    data={
                        "user_id": str(user_id),
                        "unlocked_at": user.updated_at.isoformat(),
                        "message": "Account successfully unlocked",
                    }
                )

        except Exception as exc:
            logger.error(f"unlock_account failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Account Audit History ────────────────────────────────────────────

    async def get_account_history(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
        limit: int = 100,
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get account lifecycle event history.
        
        Returns:
        - Account creation
        - Password changes
        - Email verification
        - Login history (last N)
        - Status changes (locked, deactivated, deleted)
        - Session revocations
        
        Note: This is a simplified version. Full implementation would
        query a dedicated audit_log table.
        """
        try:
            user_id = uuid.UUID(str(user_id))

            async with self.uow_service:
                user_repo: UserRepository = self.uow_service.get_repository(UserRepository)
                session_repo: UserSessionRepository = self.uow_service.get_repository(
                    UserSessionRepository
                )

                user = await user_repo.get_by_id(
                    session=self.uow_service.session,
                    id=user_id,
                )
                if not user:
                    return ServiceResult.fail(
                        error=f"User {user_id} not found",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                # Get recent sessions for login history
                sessions = await session_repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=user_id,
                )
                recent_sessions = sorted(
                    sessions,
                    key=lambda s: s.created_at if s.created_at else datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True,
                )[:limit]

                # Build timeline of events
                timeline = []

                # Account created
                if user.created_at:
                    timeline.append({
                        "event_type": "account_created",
                        "timestamp": user.created_at.isoformat(),
                        "description": "Account created",
                    })

                # Email verified
                if user.is_verified and user.email_verified_at:
                    timeline.append({
                        "event_type": "email_verified",
                        "timestamp": user.email_verified_at.isoformat(),
                        "description": "Email address verified",
                    })

                # Password changes
                if hasattr(user, 'password_changed_at') and user.password_changed_at:
                    timeline.append({
                        "event_type": "password_changed",
                        "timestamp": user.password_changed_at.isoformat(),
                        "description": "Password changed",
                    })

                # Account locked
                if user.is_locked:
                    timeline.append({
                        "event_type": "account_locked",
                        "timestamp": user.locked_until.isoformat() if user.locked_until else None,
                        "description": f"Account locked after {user.failed_login_attempts} failed login attempts",
                    })

                # Account deactivated
                if not user.is_active and hasattr(user, 'deactivated_at') and user.deactivated_at:
                    timeline.append({
                        "event_type": "account_deactivated",
                        "timestamp": user.deactivated_at.isoformat(),
                        "description": f"Account deactivated: {getattr(user, 'deactivation_reason', 'No reason provided')}",
                    })

                # Account deleted
                if user.deleted_at:
                    timeline.append({
                        "event_type": "account_deleted",
                        "timestamp": user.deleted_at.isoformat(),
                        "description": "Account marked for deletion",
                    })

                # Recent logins
                for session in recent_sessions:
                    timeline.append({
                        "event_type": "login",
                        "timestamp": session.created_at.isoformat() if session.created_at else None,
                        "description": f"Login from {getattr(session, 'device_name', 'Unknown device')}",
                        "ip_address": session.ip_address,
                        "location": getattr(session, 'location', None),
                        "session_id": str(session.id),
                    })

                # Sort timeline by timestamp
                timeline.sort(key=lambda e: e.get('timestamp', ''), reverse=True)

                return ServiceResult.ok(
                    data={
                        "user_id": str(user_id),
                        "timeline": timeline,
                        "total_events": len(timeline),
                    }
                )

        except Exception as exc:
            logger.error(f"get_account_history failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    # ─── Account Status Check ─────────────────────────────────────────────

    async def get_account_status(
        self,
        ctx: ServiceContext,
        user_id: Union[uuid.UUID, str],
    ) -> ServiceResult[Dict[str, Any]]:
        """
        Get comprehensive account status information.
        
        Returns detailed status including:
        - Basic account info
        - Security status
        - Activity metrics
        - Compliance information
        """
        try:
            user_id = uuid.UUID(str(user_id))

            async with self.uow_service:
                user_repo: UserRepository = self.uow_service.get_repository(UserRepository)
                session_repo: UserSessionRepository = self.uow_service.get_repository(
                    UserSessionRepository
                )

                user = await user_repo.get_by_id(
                    session=self.uow_service.session,
                    id=user_id,
                )
                if not user:
                    return ServiceResult.fail(
                        error=f"User {user_id} not found",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                # Get active sessions count
                sessions = await session_repo.list_user_sessions(
                    session=self.uow_service.session,
                    user_id=user_id,
                )
                active_sessions = [s for s in sessions if not s.is_revoked]

                # Determine overall status
                if user.deleted_at:
                    overall_status = AccountStatus.DELETED
                elif user.is_locked:
                    overall_status = AccountStatus.LOCKED
                elif not user.is_active:
                    overall_status = AccountStatus.DEACTIVATED
                else:
                    overall_status = AccountStatus.ACTIVE

                status_info = {
                    "user_id": str(user_id),
                    "email": user.email,
                    "overall_status": overall_status.value,
                    "account_info": {
                        "created_at": user.created_at.isoformat() if user.created_at else None,
                        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                        "is_verified": user.is_verified,
                    },
                    "security_status": {
                        "is_active": user.is_active,
                        "is_locked": user.is_locked,
                        "locked_until": user.locked_until.isoformat() if user.locked_until else None,
                        "failed_login_attempts": user.failed_login_attempts,
                        "mfa_enabled": user.mfa_enabled,
                        "change_password_required": getattr(user, 'change_password_required', False),
                    },
                    "session_info": {
                        "active_sessions_count": len(active_sessions),
                        "total_sessions_count": len(sessions),
                    },
                    "lifecycle_info": {
                        "is_deleted": user.deleted_at is not None,
                        "deleted_at": user.deleted_at.isoformat() if user.deleted_at else None,
                        "deactivated_at": getattr(user, 'deactivated_at', None),
                        "can_be_restored": user.deleted_at is not None,
                    },
                }

                return ServiceResult.ok(data=status_info)

        except Exception as exc:
            logger.error(f"get_account_status failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
