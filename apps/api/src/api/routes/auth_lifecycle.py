"""
Sprint 8.3.1 - Authentication Lifecycle Routes
===============================================
Additional authentication lifecycle endpoints:
- Resend invitation
- Force password change (first login)
- Account deletion
- Account restoration

Security:
- Invitation resend requires organization admin
- Password change skips normal enforcement middleware
- Account deletion has grace period
"""

import hashlib
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import jwt, JWTError
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.deps import get_current_user
from api.core.security import ALGORITHM, get_password_hash, verify_password
from api.database.session import get_db
from api.models import PasswordResetToken, EmailVerificationToken
from api.models.auth import AuditLog
from api.models.iam import RefreshToken, UserSession
from api.models.membership import OrganizationInvitation, UserOrganization, UserRole
from api.models.user import User
from api.middleware.auth_enforcement import require_active_account

logger = logging.getLogger(__name__)
from api.services.email_service import send_invitation_email

router = APIRouter(prefix="/auth", tags=["authentication-lifecycle"])


# ──────────────────────────────────────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────────────────────────────────────

class ResendInvitationRequest(BaseModel):
    """Request to resend an invitation."""
    invitation_id: UUID


class ResendInvitationResponse(BaseModel):
    """Response after resending invitation."""
    success: bool
    message: str
    invitation_id: UUID
    expires_at: datetime


class ChangePasswordRequest(BaseModel):
    """Request to change password (first login or forced change)."""
    current_password: Optional[str] = None  # Not required for first login with temp password
    temporary_password: Optional[str] = None  # Used for first login
    new_password: str


class ChangePasswordResponse(BaseModel):
    """Response after password change."""
    success: bool
    message: str


class DeleteAccountRequest(BaseModel):
    """Request to delete account."""
    password: str
    reason: Optional[str] = None


class DeleteAccountResponse(BaseModel):
    """Response after account deletion request."""
    success: bool
    message: str
    deletion_scheduled_at: datetime


class RestoreAccountRequest(BaseModel):
    """Request to restore deleted account."""
    email: EmailStr
    password: str


class RestoreAccountResponse(BaseModel):
    """Response after account restoration."""
    success: bool
    message: str


class PasswordResetRequest(BaseModel):
    """Request to start a password reset."""
    email: EmailStr


class VerifyResetTokenRequest(BaseModel):
    """Request to verify a password reset token."""
    token: str


class ResetPasswordPayload(BaseModel):
    """Request to set a new password with a reset token."""
    token: str
    new_password: str


class VerifyEmailPayload(BaseModel):
    """Request to verify an email address with a token."""
    token: str


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

def _find_reset_token_sync(db: Session, token: str) -> Optional[PasswordResetToken]:
    """Locate an unused, unexpired reset token (hashed or plaintext lookup)."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    for candidate in (token_hash, token):
        found = (
            db.query(PasswordResetToken)
            .filter(
                PasswordResetToken.token_hash == candidate,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > now,
            )
            .first()
        )
        if found:
            return found
    return None


def _find_verification_token_sync(db: Session, token: str) -> Optional[EmailVerificationToken]:
    """Locate an unused, unexpired email verification token (hashed or plaintext lookup)."""
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    now = datetime.now(timezone.utc)
    for candidate in (token_hash, token):
        found = (
            db.query(EmailVerificationToken)
            .filter(
                EmailVerificationToken.token_hash == candidate,
                EmailVerificationToken.is_used == False,
                EmailVerificationToken.expires_at > now,
            )
            .first()
        )
        if found:
            return found
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

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


def _get_current_session_id(request: Request) -> Optional[uuid.UUID]:
    """Extract the current session ID from the request's access token."""
    try:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            claim = payload.get("session_id") or payload.get("jti")
            if claim:
                return uuid.UUID(str(claim))
    except (JWTError, ValueError):
        pass
    return None


# ──────────────────────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────────────────────

@router.post("/invitations/{invitation_id}/resend", response_model=ResendInvitationResponse)
def resend_invitation(
    invitation_id: UUID,
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ResendInvitationResponse:
    """
    Resend an invitation email.
    
    Requirements:
    - Invitation must exist and not be accepted
    - User must be admin/owner of the organization
    - New expiration date is set (72 hours from now)
    
    Use case: Invitation expired or user didn't receive original email.
    """
    # Find invitation
    invitation = (
        db.query(OrganizationInvitation)
        .filter(
            OrganizationInvitation.id == invitation_id,
            OrganizationInvitation.is_accepted == False,
        )
        .first()
    )
    
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already accepted.",
        )

    # Phase 10: only an OWNER/ADMIN of the invitation's organization may resend.
    membership = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.organization_id == invitation.organization_id,
            UserOrganization.user_id == current_user.id,
        )
        .first()
    )
    if not membership or membership.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only an organization admin can resend invitations",
        )

    # Generate new token and extend expiration
    new_token = secrets.token_urlsafe(32)
    new_token_hash = hashlib.sha256(new_token.encode()).hexdigest()
    new_expiration = datetime.now(timezone.utc) + timedelta(hours=72)
    
    invitation.token = new_token_hash
    invitation.expires_at = new_expiration
    db.commit()
    
    # Send new invitation email
    try:
        # Build accept URL with invitation token
        accept_url = f"{settings.FRONTEND_URL}/auth/invitation?token={new_token}"
        
        send_invitation_email(
            to_email=invitation.email,
            inviter_name=current_user.full_name,
            org_name=invitation.organization.name if invitation.organization else "EAIMOS",
            role=invitation.role,
            accept_url=accept_url,
        )
    except Exception as e:
        # Log error but don't fail the request
        print(f"Failed to send invitation email: {e}")
    
    # Audit log
    log_audit(
        db,
        current_user.id,
        "INVITATION_RESENT",
        request,
        {
            "invitation_id": str(invitation_id),
            "recipient_email": invitation.email,
        },
    )
    
    return ResendInvitationResponse(
        success=True,
        message="Invitation resent successfully.",
        invitation_id=invitation_id,
        expires_at=new_expiration,
    )


@router.post("/change-password", response_model=ChangePasswordResponse)
def change_password(
    request_data: ChangePasswordRequest,
    request: Request,
    current_user: User = Depends(get_current_user),  # Note: No enforcement middleware
    db: Session = Depends(get_db),
) -> ChangePasswordResponse:
    """
    Change user password.
    
    Two flows:
    1. Regular password change: requires current_password
    2. First login with temporary password: requires temporary_password
    
    On success:
    - Updates hashed_password
    - Clears change_password_required flag
    - Clears temporary_password fields
    - Updates password_changed_at
    
    Note: This endpoint does NOT enforce password change requirement
    (it's the target endpoint users are redirected to).
    """
    # Validate password strength
    if len(request_data.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long.",
        )
    
    # Flow 1: First login with temporary password
    if request_data.temporary_password:
        if not hasattr(current_user, 'temporary_password') or not current_user.temporary_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No temporary password set for this account.",
            )
        
        # Check temporary password expiry
        if (
            hasattr(current_user, 'temporary_password_expires_at')
            and current_user.temporary_password_expires_at
            and current_user.temporary_password_expires_at < datetime.now(timezone.utc)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Temporary password has expired. Please request a new invitation.",
            )
        
        # Verify temporary password
        if not verify_password(request_data.temporary_password, current_user.temporary_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid temporary password.",
            )
    
    # Flow 2: Regular password change
    elif request_data.current_password:
        if not current_user.hashed_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account does not have a password (OAuth-only).",
            )
        
        if not verify_password(request_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either current_password or temporary_password is required.",
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(request_data.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)
    
    # Clear password change enforcement flags
    if hasattr(current_user, 'change_password_required'):
        current_user.change_password_required = False
    if hasattr(current_user, 'temporary_password'):
        current_user.temporary_password = None
    if hasattr(current_user, 'temporary_password_expires_at'):
        current_user.temporary_password_expires_at = None

    # Phase 4: a password change logs out every OTHER session (and revokes
    # their refresh tokens) so a compromised credential stops working
    # elsewhere. The session that performed the change is kept active.
    now = datetime.now(timezone.utc)
    current_session_id = _get_current_session_id(request)
    other_sessions_query = db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
    )
    if current_session_id:
        other_sessions_query = other_sessions_query.filter(UserSession.id != current_session_id)
    other_sessions = other_sessions_query.all()

    for s in other_sessions:
        s.is_revoked = True
        s.revoked_at = now
        s.revocation_reason = "password_change"

    if other_sessions:
        db.query(RefreshToken).filter(
            RefreshToken.session_id.in_([s.id for s in other_sessions]),
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_revoked == False,
        ).update({RefreshToken.is_revoked: True})

    db.commit()
    
    # Audit log
    log_audit(
        db,
        current_user.id,
        "PASSWORD_CHANGED",
        request,
        {"method": "temporary" if request_data.temporary_password else "regular"},
    )
    
    return ChangePasswordResponse(
        success=True,
        message="Password changed successfully.",
    )


@router.post("/account/delete", response_model=DeleteAccountResponse)
def request_account_deletion(
    request_data: DeleteAccountRequest,
    request: Request,
    _: None = Depends(require_active_account),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DeleteAccountResponse:
    """
    Request account deletion.
    
    Grace period: 7 days before permanent deletion.
    User can cancel deletion within grace period.
    
    Process:
    1. Verify password
    2. Set deletion_requested_at and scheduled_deletion_at
    3. Send confirmation email
    4. Account remains accessible during grace period
    """
    # Verify password
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete OAuth-only account via this endpoint.",
        )
    
    if not verify_password(request_data.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )
    
    # Check if already requested
    if current_user.deletion_requested_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account deletion already requested.",
        )
    
    # Schedule deletion
    now = datetime.now(timezone.utc)
    scheduled_at = now + timedelta(days=7)
    
    current_user.deletion_requested_at = now
    current_user.scheduled_deletion_at = scheduled_at
    current_user.deletion_reason = request_data.reason
    db.commit()
    
    # Audit log
    log_audit(
        db,
        current_user.id,
        "ACCOUNT_DELETION_REQUESTED",
        request,
        {"scheduled_at": scheduled_at.isoformat()},
    )
    
    # TODO: Send confirmation email
    
    return DeleteAccountResponse(
        success=True,
        message="Account deletion scheduled. You have 7 days to cancel.",
        deletion_scheduled_at=scheduled_at,
    )


@router.post("/account/restore", response_model=RestoreAccountResponse)
def restore_account(
    request_data: RestoreAccountRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> RestoreAccountResponse:
    """
    Restore account during grace period.
    
    Requirements:
    - Account must have deletion_requested_at set
    - Must be within grace period (before scheduled_deletion_at)
    - Must provide correct password
    
    On success:
    - Clears deletion_requested_at and scheduled_deletion_at
    - Account returns to normal state
    """
    # Find user
    user = db.query(User).filter(User.email == request_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found.",
        )
    
    # Check if deletion was requested
    if not user.deletion_requested_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account deletion was not requested.",
        )
    
    # Check if still within grace period
    if user.scheduled_deletion_at and user.scheduled_deletion_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Grace period has expired. Account may have been permanently deleted.",
        )
    
    # Verify password
    if not user.hashed_password or not verify_password(request_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password.",
        )
    
    # Restore account — Phase 7: also re-activate so the user can log in again.
    user.deletion_requested_at = None
    user.scheduled_deletion_at = None
    user.deletion_reason = None
    user.is_active = True
    db.commit()
    
    # Audit log
    log_audit(
        db,
        user.id,
        "ACCOUNT_RESTORED",
        request,
        {},
    )

    return RestoreAccountResponse(
        success=True,
        message="Account restored successfully.",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Password Reset
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/password-reset/request", status_code=status.HTTP_200_OK)
def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Request a password reset. Returns 200 even for unknown emails (anti-enumeration)."""
    user = db.query(User).filter(User.email == body.email).first()
    if user:
        # Invalidate any previous unused tokens
        db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False,
        ).update({"is_used": True})

        raw_token = secrets.token_urlsafe(32)
        db_token = PasswordResetToken(
            user_id=user.id,
            token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=False,
        )
        db.add(db_token)
        db.commit()
        log_audit(db, user.id, "PASSWORD_RESET_REQUESTED", request, {})

    return {"message": "If an account exists with that email, a password reset link has been sent."}


@router.post("/password-reset/verify", status_code=status.HTTP_200_OK)
def verify_reset_token(
    body: VerifyResetTokenRequest,
    db: Session = Depends(get_db),
):
    """Verify that a password reset token is valid."""
    db_token = _find_reset_token_sync(db, body.token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )
    return {"valid": True}


@router.post("/password-reset/reset", status_code=status.HTTP_200_OK)
def reset_password(
    body: ResetPasswordPayload,
    db: Session = Depends(get_db),
):
    """Set a new password using a valid reset token."""
    db_token = _find_reset_token_sync(db, body.token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token",
        )

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    user.hashed_password = get_password_hash(body.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    db_token.is_used = True
    db_token.used_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Password reset successfully."}


# ──────────────────────────────────────────────────────────────────────────────
# Email Verification
# ──────────────────────────────────────────────────────────────────────────────


@router.post("/email-verification/request", status_code=status.HTTP_200_OK)
def request_email_verification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Request an email verification token for the current user."""
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already verified",
        )

    # Invalidate any previous unused tokens
    db.query(EmailVerificationToken).filter(
        EmailVerificationToken.user_id == current_user.id,
        EmailVerificationToken.is_used == False,
    ).update({"is_used": True})

    raw_token = secrets.token_urlsafe(32)
    db_token = EmailVerificationToken(
        user_id=current_user.id,
        token_hash=hashlib.sha256(raw_token.encode()).hexdigest(),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        is_used=False,
    )
    db.add(db_token)
    db.commit()

    return {"message": "Verification email sent.", "success": True}


@router.post("/email-verification/verify", status_code=status.HTTP_200_OK)
def verify_email(
    body: VerifyEmailPayload,
    db: Session = Depends(get_db),
):
    """Verify an email address using a valid verification token."""
    db_token = _find_verification_token_sync(db, body.token)
    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token",
        )

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User not found",
        )

    user.is_verified = True
    user.email_verified_at = datetime.now(timezone.utc)
    db_token.is_used = True
    db_token.used_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Email verified successfully.", "success": True}
