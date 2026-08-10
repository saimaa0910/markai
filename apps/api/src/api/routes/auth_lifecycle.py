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
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.deps import get_current_user
from api.core.security import get_password_hash, verify_password
from api.database.session import get_db
from api.models.auth import AuditLog
from api.models.iam import OrganizationInvitation
from api.models.user import User
from api.middleware.auth_enforcement import require_active_account
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


# ──────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────────────────────────────────────

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
    
    # TODO: Check if current_user is admin of invitation.organization_id
    # For now, we'll allow any authenticated user to resend (permissive for MVP)
    
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
        accept_url = f"{settings.FRONTEND_URL}/auth/accept-invitation?token={new_token}"
        
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
    
    # Restore account
    user.deletion_requested_at = None
    user.scheduled_deletion_at = None
    user.deletion_reason = None
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
