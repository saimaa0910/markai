"""
Sprint 8.3.1 - Authentication Enforcement Middleware
=====================================================
Enforces authentication lifecycle policies:
- Force password change on first login or after admin reset
- Block deactivated accounts
- Block deleted accounts (soft delete)
- Validate account status before allowing API access

Usage in routes:
    from api.middleware.auth_enforcement import require_active_account, enforce_password_change
    
    @router.get("/protected")
    def protected_route(
        _: None = Depends(require_active_account),
        current_user: User = Depends(get_current_user),
    ):
        ...

Routes that should skip enforcement:
- /auth/login (login flow)
- /auth/change-password (the change password endpoint itself)
- /auth/logout
- /auth/register
- Public routes
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.user import User


class AuthEnforcementError(HTTPException):
    """Base exception for authentication enforcement failures."""
    pass


class PasswordChangeRequiredError(AuthEnforcementError):
    """User must change password before accessing other endpoints."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "password_change_required",
                "message": "You must change your password before continuing.",
                "required_action": "POST /auth/change-password",
            },
        )


class AccountDeactivatedError(AuthEnforcementError):
    """Account has been administratively deactivated."""
    def __init__(self, reason: Optional[str] = None):
        detail = {
            "error": "account_deactivated",
            "message": "Your account has been deactivated.",
        }
        if reason:
            detail["reason"] = reason
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class AccountDeletedError(AuthEnforcementError):
    """Account has been soft-deleted."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "account_deleted",
                "message": "Your account has been deleted.",
            },
        )


class AccountInactiveError(AuthEnforcementError):
    """Account is marked as inactive."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "account_inactive",
                "message": "Your account is inactive. Please contact support.",
            },
        )


class AccountLockedError(AuthEnforcementError):
    """Account is temporarily locked due to failed login attempts."""
    def __init__(self, locked_until: datetime):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "account_locked",
                "message": "Your account is temporarily locked due to too many failed login attempts.",
                "locked_until": locked_until.isoformat(),
            },
        )


class TemporaryPasswordExpiredError(AuthEnforcementError):
    """Temporary password (from invitation) has expired."""
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "temporary_password_expired",
                "message": "Your temporary password has expired. Please request a new invitation.",
            },
        )


def check_account_status(user: User) -> None:
    """
    Validate account is in good standing.
    
    Raises:
        AccountDeletedError: If account is soft-deleted
        AccountDeactivatedError: If account is administratively deactivated
        AccountInactiveError: If is_active = False
        AccountLockedError: If account is temporarily locked
    """
    # Check soft delete (deleted_at from Base)
    if hasattr(user, 'deleted_at') and user.deleted_at is not None:
        raise AccountDeletedError()
    
    # Check administrative deactivation
    if hasattr(user, 'account_deactivated_at') and user.account_deactivated_at is not None:
        raise AccountDeactivatedError(reason=getattr(user, 'account_deactivated_reason', None))
    
    # Check is_active flag
    if not user.is_active:
        raise AccountInactiveError()
    
    # Check account lockout
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise AccountLockedError(locked_until=user.locked_until)


def check_password_change_required(user: User) -> None:
    """
    Check if user must change password.
    
    Raises:
        PasswordChangeRequiredError: If change_password_required is True
    """
    if hasattr(user, 'change_password_required') and user.change_password_required:
        raise PasswordChangeRequiredError()


def check_temporary_password_expiry(user: User) -> None:
    """
    Check if temporary password (from invitation) has expired.
    
    Raises:
        TemporaryPasswordExpiredError: If temporary password is set but expired
    """
    if hasattr(user, 'temporary_password') and user.temporary_password:
        if hasattr(user, 'temporary_password_expires_at') and user.temporary_password_expires_at:
            if user.temporary_password_expires_at < datetime.now(timezone.utc):
                raise TemporaryPasswordExpiredError()


def require_active_account(
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Dependency that enforces account is active and in good standing.
    
    Use this on all protected routes (except auth endpoints).
    
    Raises:
        AccountDeletedError, AccountDeactivatedError, AccountInactiveError, AccountLockedError
    """
    check_account_status(current_user)


def enforce_password_change(
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Dependency that enforces password change if required.
    
    Use this on protected routes that should block users who need to change password.
    Typically, only the change-password endpoint itself should skip this.
    
    Raises:
        PasswordChangeRequiredError
    """
    # First check account status
    check_account_status(current_user)
    # Then check password change requirement
    check_password_change_required(current_user)


def enforce_all_auth_policies(
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Dependency that enforces ALL authentication policies:
    - Account status (active, not deleted, not deactivated)
    - Password change requirement
    - Temporary password expiry
    
    Use this as the default enforcement on most protected routes.
    
    Raises:
        AuthEnforcementError (any subclass)
    """
    check_account_status(current_user)
    check_password_change_required(current_user)
    check_temporary_password_expiry(current_user)


# Convenience exports
__all__ = [
    "require_active_account",
    "enforce_password_change",
    "enforce_all_auth_policies",
    "check_account_status",
    "check_password_change_required",
    "check_temporary_password_expiry",
    "AuthEnforcementError",
    "PasswordChangeRequiredError",
    "AccountDeactivatedError",
    "AccountDeletedError",
    "AccountInactiveError",
    "AccountLockedError",
    "TemporaryPasswordExpiredError",
]
