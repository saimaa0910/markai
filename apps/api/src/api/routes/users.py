import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status, Header, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.security import verify_password
from api.database.session import get_db
from api.core.deps import get_current_user
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
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
    db: Session = Depends(get_db),
) -> Any:
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
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
) -> Any:
    """
    List all users in the system.
    """
    org_uuid = None
    if x_organization_id:
        try:
            org_uuid = uuid.UUID(x_organization_id)
        except ValueError:
            pass
    
    users = db.query(User).all()
    return [resolve_user_response(u, db, org_uuid) for u in users]


@router.patch("/me", response_model=UserResponse)
def update_my_profile(
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
) -> Any:
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
def upload_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
) -> Any:
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
def update_preferences(
    preferences_in: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
) -> Any:
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
def change_email(
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
def confirm_email_change(
    request_body: ConfirmEmailChangeRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Confirm email change using the token sent to the new address.
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
def update_user(
    user_id: uuid.UUID,
    user_in: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    x_organization_id: Optional[str] = Header(None),
) -> Any:
    """
    Update a specific user profile (e.g. deactivate active status).
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
def delete_my_account(
    body: DeleteAccountRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
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
) -> None:
    """
    Delete a specific user account.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    db.delete(user)
    db.commit()



# ─── Change Email ─────────────────────────────────────────────────────────────

class ChangeEmailRequest(BaseModel):
    new_email: str
    password: str


@router.patch("/email", response_model=dict)
def change_email(
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
    from api.core.security import create_access_token, verify_password
    from api.core.config import settings
    from api.services.email_service import send_change_email_verification
    import re

    # Validate email format
    if not re.match(r'^[^@]+@[^@]+\.[^@]+$', body.new_email):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid email format")

    # Verify password
    if not current_user.hashed_password or not verify_password(body.password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect password")

    # Check new email not taken
    existing = db.query(User).filter(User.email == body.new_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already in use")

    # Store pending email in preferences
    prefs = current_user.preferences or {}
    prefs["pending_email"] = body.new_email
    current_user.preferences = prefs
    db.commit()

    # Create email change token (encodes both user_id and new email)
    import json, base64
    payload_data = json.dumps({"user_id": str(current_user.id), "new_email": body.new_email})
    encoded = base64.urlsafe_b64encode(payload_data.encode()).decode()
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
def confirm_email_change(
    token: str,
    new_email: str,
    request: Request,
    db: Session = Depends(get_db),
) -> Any:
    """
    Confirm email change using the token sent to the new address.
    """
    from api.core.security import ALGORITHM
    from api.core.config import settings
    from jose import jwt, JWTError
    import uuid

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(str(payload.get("sub")))
    except (JWTError, ValueError):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    prefs = user.preferences or {}
    pending_email = prefs.get("pending_email")
    if not pending_email or pending_email != new_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email change request not found or mismatch")

    # Check new email still available
    existing = db.query(User).filter(User.email == new_email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email address is already taken")

    user.email = new_email
    user.is_verified = True
    prefs.pop("pending_email", None)
    user.preferences = prefs
    db.commit()

    return {"success": True, "message": "Email address updated successfully"}
