import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header, UploadFile, File
from sqlalchemy.orm import Session

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
