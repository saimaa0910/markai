import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.security import verify_password
from api.core.config import settings
from api.database.session import get_db
from api.core.deps import get_current_user, get_current_admin_user
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1
from api.models.user import User
from api.models.membership import UserOrganization
from api.models.auth import Role
from api.schemas.user import UserResponse, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


def resolve_user_response(user: User, db: Session, org_id: Optional[uuid.UUID] = None) -> dict:
    membership = None
    if org_id:
        membership = (
            db.query(UserOrganization)
            .filter(
                UserOrganization.user_id == user.id,
                UserOrganization.organization_id == org_id,
            )
            .first()
        )
    if not membership:
        membership = (
            db.query(UserOrganization)
            .filter(UserOrganization.user_id == user.id)
            .first()
        )

    role_name = "MEMBER"
    permissions = []
    if membership:
        role_name = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        db_role = db.query(Role).filter(Role.name == role_name).first()
        if db_role:
            permissions = [p.name for p in db_role.permissions]

    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "role": role_name,
        "permissions": permissions,
        "avatar": (user.preferences or {}).get("avatar_url") or f"https://api.dicebear.com/7.x/initials/svg?seed={user.full_name}",
        "preferences": user.preferences or {"theme": "dark", "notifications": True},
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(  # Sprint 8.3.1
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Get profile details of the currently authenticated user.
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass
    return resolve_user_response(current_user, db, org_uuid)


@router.get("/", response_model=List[UserResponse])
def list_users(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    List users. Phase 17: scope to the current user's organizations unless the
    caller is a superuser (who may list the entire system). Previously any
    authenticated user (including guests) could enumerate every account.
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass

    if current_user.is_superuser:
        users = db.query(User).all()
    else:
        org_ids = [
            m.organization_id
            for m in db.query(UserOrganization).filter(UserOrganization.user_id == current_user.id).all()
        ]
        if not org_ids:
            return []
        user_ids = [
            m.user_id
            for m in db.query(UserOrganization).filter(UserOrganization.organization_id.in_(org_ids)).all()
        ]
        users = db.query(User).filter(User.id.in_(user_ids)).all()
    return [resolve_user_response(u, db, org_uuid) for u in users]


@router.patch("/me", response_model=UserResponse)
def update_my_profile(  # Sprint 8.3.1
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Update my own profile.
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass

    update_data = user_in.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        if field == "password" and val:
            from api.core.security import get_password_hash
            current_user.hashed_password = get_password_hash(val)
        else:
            setattr(current_user, field, val)

    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return resolve_user_response(current_user, db, org_uuid)


@router.post("/me/avatar", response_model=UserResponse)
def upload_avatar(  # Sprint 8.3.1
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Upload profile avatar.
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass

    avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={current_user.full_name}_{file.filename}"
    prefs = current_user.preferences or {}
    prefs["avatar_url"] = avatar_url
    current_user.preferences = prefs
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return resolve_user_response(current_user, db, org_uuid)


@router.patch("/me/preferences", response_model=UserResponse)
def update_preferences(  # Sprint 8.3.1
    preferences_in: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Update my profile preferences.
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass

    current_prefs = current_user.preferences or {}
    for k, v in preferences_in.items():
        current_prefs[k] = v

    current_user.preferences = current_prefs
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return resolve_user_response(current_user, db, org_uuid)


class ChangeEmailRequest(BaseModel):
    new_email: str
    password: str


class ConfirmEmailChangeRequest(BaseModel):
    token: str
    new_email: str


@router.patch("/email", response_model=dict)
def change_email(  # Sprint 8.3.1
    body: ChangeEmailRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Request email change. Sends verification link to the new address.
    The old email remains active until the new one is verified.
    """
    from datetime import timedelta
    from api.core.security import create_access_token
    from api.core.config import settings
    from api.services.email_service import send_change_email_verification
    import re

    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', body.new_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    if not current_user.hashed_password or not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    existing = db.query(User).filter(User.email == body.new_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already in use")

    prefs = current_user.preferences or {}
    prefs["pending_email"] = body.new_email
    current_user.preferences = prefs
    db.commit()

    token = create_access_token(current_user.id, expires_delta=timedelta(days=1))
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email-change?token={token}&email={body.new_email}"

    try:
        send_change_email_verification(body.new_email, current_user.full_name, verify_url)
    except Exception as e:
        import logging
        logging.getLogger("eaimos.users").error(f"Failed to send change email verification: {e}")

    return {
        "success": True,
        "message": f"Verification email sent to {body.new_email}. Click the link to confirm your new email address.",
    }


@router.post("/email/confirm", response_model=dict)
def confirm_email_change(  # Sprint 8.3.1
    request_body: ConfirmEmailChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Confirm email change using the token sent to the new address.
    The emailed JWT is the sole authorization; no extra bearer token is
    expected here (Phase 10).
    """
    from api.core.security import ALGORITHM
    from api.core.config import settings
    from jose import jwt, JWTError
    import uuid

    try:
        payload = jwt.decode(request_body.token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(str(payload.get("sub")))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    prefs = user.preferences or {}
    pending_email = prefs.get("pending_email")
    if not pending_email or pending_email != request_body.new_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email change request not found or mismatch")

    existing = db.query(User).filter(User.email == request_body.new_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already taken")

    user.email = request_body.new_email
    user.is_verified = True
    prefs.pop("pending_email", None)
    user.preferences = prefs
    db.commit()

    return {"success": True, "message": "Email address updated successfully"}


@router.patch("/{user_id}", response_model=UserResponse)
def update_user(  # Sprint 8.3.1
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin_user),
    x_organization_id: Optional[str] = Header(None),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Update a specific user profile. Phase 17: admin/superuser only. Only
    non-privileged fields may be modified (identity & role fields are locked).
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    update_data = user_in.model_dump(exclude_unset=True)
    # Phase 17: deny privilege-escalation fields entirely. `model_extra`
    # captures any fields Pydantic strips out of `update_data`.
    forbidden = {"email", "is_superuser", "hashed_password", "password", "role"}
    extra_fields = user_in.model_extra or {}
    if any(f in forbidden for f in list(update_data.keys()) + list(extra_fields.keys())):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Field cannot be modified through this endpoint",
        )
    for field, val in update_data.items():
        if field == "password" and val:
            from api.core.security import get_password_hash
            user.hashed_password = get_password_hash(val)
        else:
            setattr(user, field, val)

    db.add(user)
    db.commit()
    db.refresh(user)
    return resolve_user_response(user, db, org_uuid)


# ─── Self Account Deletion ────────────────────────────────────────────────────

class DeleteAccountRequest(BaseModel):
    password: str
    confirmation: str  # Must equal "DELETE"


@router.delete("/me", status_code=status.HTTP_200_OK)
def delete_my_account(  # Sprint 8.3.1
    body: DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Self-delete the authenticated user's account.
    Requires password confirmation and the string 'DELETE'.
    """
    from pydantic import BaseModel
    if body.confirmation != "DELETE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Confirmation must be 'DELETE'",
        )
    if not current_user.hashed_password or not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect password",
        )
    # Soft delete: deactivate account
    current_user.is_active = False
    from datetime import datetime, timezone
    current_user.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "message": "Account has been deactivated. Contact support to restore it."}


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _auth: None = Depends(enforce_all_auth_policies),
) -> None:
    """Admin-only deletion of a user account."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators can delete user accounts",
        )
    target_user = db.query(User).filter(User.id == user_id).first()
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    db.delete(target_user)
    db.commit()
    return None


# ─── Account Deletion (7-Day Recovery Window) ────────────────────────────────

class DeleteAccountRequest(BaseModel):
    reason: Optional[str] = None
    confirm: bool  # Must be True


@router.post("/me/delete", status_code=status.HTTP_200_OK)
def request_account_deletion(  # Sprint 8.3.1
    body: DeleteAccountRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """
    Initiate account deletion with a 7-day recovery window.
    Account is immediately deactivated (login disabled).
    Permanent deletion scheduled for 7 days from now.
    """
    from datetime import timedelta, timezone
    from api.services.email_service import send_account_deletion_scheduled_email

    if not body.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must confirm account deletion by setting confirm=true",
        )

    if current_user.deletion_requested_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account deletion already requested",
        )

    now = datetime.now(timezone.utc)
    deletion_date = now + timedelta(days=7)

    current_user.deletion_requested_at = now
    current_user.scheduled_deletion_at = deletion_date
    current_user.deletion_reason = body.reason
    current_user.is_active = False  # Disable login immediately

    db.commit()

    # Revoke all active sessions
    from api.models.auth import RefreshToken
    from api.models.iam import UserSession
    db.query(RefreshToken).filter(
        RefreshToken.user_id == current_user.id,
        RefreshToken.is_revoked == False,
    ).update({RefreshToken.is_revoked: True})
    db.query(UserSession).filter(
        UserSession.user_id == current_user.id,
        UserSession.is_revoked == False,
    ).update({UserSession.is_revoked: True})
    db.commit()

    # Log audit
    from api.models.platform_events import AuditLog
    audit = AuditLog(
        actor_id=current_user.id,
        action="ACCOUNT_DELETION_REQUESTED",
        entity_type="users",
        entity_id=current_user.id,
        description=f"Account deletion requested. Permanent deletion scheduled for {deletion_date.date()}",
        risk_level="high",
    )
    db.add(audit)
    db.commit()

    # Send notification
    restore_url = f"{settings.FRONTEND_URL}/auth/restore-account?user_id={current_user.id}"
    try:
        send_account_deletion_scheduled_email(
            current_user.email,
            current_user.full_name,
            deletion_date.strftime("%B %d, %Y"),
            restore_url,
        )
    except Exception:
        pass

    return {
        "success": True,
        "message": "Account deletion initiated. Your account will be permanently deleted in 7 days.",
        "deletion_scheduled_at": deletion_date.isoformat(),
        "restore_deadline": deletion_date.isoformat(),
    }


from api.core.deps import get_current_user, get_current_user_allow_inactive


@router.post("/me/restore", status_code=status.HTTP_200_OK)
def restore_account(  # Sprint 8.3.1
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_allow_inactive),
) -> Any:
    """
    Cancel pending account deletion. Must be called within the 7-day window.
    Requires authentication (user must still know their credentials).

    Phase 7: NOT gated by enforce_all_auth_policies — deactivated / inactive
    users must be able to restore without tripping the account-status block.
    """
    from api.services.email_service import send_account_restored_email

    if not current_user.deletion_requested_at:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending account deletion found",
        )

    now = datetime.now(timezone.utc)
    scheduled = current_user.scheduled_deletion_at
    if scheduled:
        if scheduled.tzinfo is None:
            scheduled = scheduled.replace(tzinfo=timezone.utc)
        if scheduled < now:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Account deletion window has passed. Account has been permanently deleted.",
            )

    # Restore
    current_user.deletion_requested_at = None
    current_user.scheduled_deletion_at = None
    current_user.deletion_reason = None
    current_user.is_active = True
    db.commit()

    from api.models.platform_events import AuditLog
    audit = AuditLog(
        actor_id=current_user.id,
        action="ACCOUNT_DELETION_RESTORED",
        entity_type="users",
        entity_id=current_user.id,
        description="Account deletion cancelled and account restored",
        risk_level="medium",
    )
    db.add(audit)
    db.commit()

    try:
        send_account_restored_email(current_user.email, current_user.full_name)
    except Exception:
        pass

    return {"success": True, "message": "Account deletion cancelled. Your account has been restored."}


@router.get("/me/deletion-status", status_code=status.HTTP_200_OK)
def get_deletion_status(  # Sprint 8.3.1
    current_user: User = Depends(get_current_user_allow_inactive),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Get current account deletion status."""
    if not current_user.deletion_requested_at:
        return {"pending_deletion": False}

    now = datetime.now(timezone.utc)
    scheduled = current_user.scheduled_deletion_at
    if scheduled and scheduled.tzinfo is None:
        scheduled = scheduled.replace(tzinfo=timezone.utc)

    days_remaining = None
    if scheduled:
        delta = scheduled - now
        days_remaining = max(0, delta.days)

    return {
        "pending_deletion": True,
        "deletion_requested_at": current_user.deletion_requested_at.isoformat() if current_user.deletion_requested_at else None,
        "scheduled_deletion_at": scheduled.isoformat() if scheduled else None,
        "days_remaining": days_remaining,
        "can_restore": days_remaining is not None and days_remaining > 0,
    }


# ─── Admin User Management ────────────────────────────────────────────────────

@router.post("/{user_id}/suspend", status_code=status.HTTP_200_OK)
def admin_suspend_user(  # Sprint 8.3.1
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Suspend a user account (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    target.is_active = False
    db.commit()

    from api.models.platform_events import AuditLog
    audit = AuditLog(
        actor_id=current_user.id,
        action="USER_SUSPENDED",
        entity_type="users",
        entity_id=user_id,
        description=f"User {target.email} suspended by admin",
        risk_level="high",
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"User {target.email} suspended"}


@router.post("/{user_id}/restore-admin", status_code=status.HTTP_200_OK)
def admin_restore_user(  # Sprint 8.3.1
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Restore a suspended user account (admin only)."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    target.is_active = True
    target.deletion_requested_at = None
    target.scheduled_deletion_at = None
    db.commit()

    from api.models.platform_events import AuditLog
    audit = AuditLog(
        actor_id=current_user.id,
        action="USER_RESTORED",
        entity_type="users",
        entity_id=user_id,
        description=f"User {target.email} restored by admin",
        risk_level="medium",
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"User {target.email} restored"}


@router.post("/{user_id}/reset-password-admin", status_code=status.HTTP_200_OK)
def admin_reset_user_password(  # Sprint 8.3.1
    user_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Admin-initiated password reset — sends reset email to user."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Superuser access required")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    from api.core.security import create_access_token
    from api.core.config import settings
    token = create_access_token(target.id, expires_delta=timedelta(hours=2))
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

    from api.services.email_service import send_password_reset_email
    try:
        send_password_reset_email(target.email, target.full_name, reset_url)
    except Exception:
        pass

    from api.models.platform_events import AuditLog
    audit = AuditLog(
        actor_id=current_user.id,
        action="ADMIN_PASSWORD_RESET",
        entity_type="users",
        entity_id=user_id,
        description=f"Password reset email sent to {target.email} by admin",
        risk_level="medium",
    )
    db.add(audit)
    db.commit()

    return {"success": True, "message": f"Password reset email sent to {target.email}"}


@router.get("/{user_id}/activity", status_code=status.HTTP_200_OK)
def get_user_activity(  # Sprint 8.3.1
    user_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    limit: int = 50,  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    """Get recent audit log activity for a user (admin or self)."""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    from api.models.platform_events import AuditLog
    logs = (
        db.query(AuditLog)
        .filter(AuditLog.actor_id == user_id)
        .order_by(AuditLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": str(log.id),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "description": log.description,
            "risk_level": log.risk_level,
            "actor_ip": log.actor_ip,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]
