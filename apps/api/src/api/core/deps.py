import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import Depends, HTTPException, Header, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.security import ALGORITHM
from api.database.session import get_db
from api.models.user import User
from api.models.membership import UserOrganization, UserRole
from api.models.iam import UserSession

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    """
    Dependency that decodes access token and retrieves user model.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
            )
        user_id = payload.get("sub")
        session_ref = payload.get("session_id") or payload.get("jti")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.id == user_uuid, User.is_active).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    if session_ref:
        try:
            session_uuid = uuid.UUID(str(session_ref))
        except ValueError:
            session_uuid = None

        if session_uuid:
            session = db.query(UserSession).filter(
                UserSession.id == session_uuid,
                UserSession.user_id == user.id,
            ).first()
            if session:
                expires_at = session.expires_at
                if expires_at.tzinfo is None:
                    expires_at = expires_at.replace(tzinfo=timezone.utc)
                if session.is_revoked or expires_at < datetime.now(timezone.utc):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Session has expired or been revoked",
                    )
                session.last_active_at = datetime.now(timezone.utc)
                db.add(session)
                db.commit()
    return user


def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Dependency that ensures the authenticated user is a superuser (admin).
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user does not have enough privileges",
        )
    return current_user


def get_current_user_allow_inactive(
    db: Session = Depends(get_db), token: str = Depends(reusable_oauth2)
) -> User:
    """
    Dependency that decodes access token and retrieves user model even if inactive.
    Used by restore-account and deletion-status endpoints.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )
        user_uuid = uuid.UUID(str(user_id))
    except (JWTError, ValidationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )

    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return user



def get_active_organization_id(
    x_organization_id: Optional[str] = Header(None),
) -> Optional[str]:
    """
    Extract active organization from X-Organization-ID request header.
    """
    return x_organization_id


def get_user_org_membership(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOrganization:
    """
    Get the current user's active organization membership.
    Raises 403 if user is not a member of any organization.
    """
    membership = (
        db.query(UserOrganization)
        .filter(UserOrganization.user_id == current_user.id)
        .filter(UserOrganization.is_revoked == False)
        .first()
    )
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not a member of any organization",
        )
    return membership


class RoleChecker:
    """
    Dependency that enforces specific role memberships in active organizations.
    """

    def __init__(self, allowed_roles: List[UserRole]) -> None:
        self.allowed_roles = allowed_roles

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        org_id: Optional[str] = Depends(get_active_organization_id),
        db: Session = Depends(get_db),
    ) -> UserOrganization:
        if not org_id:
            membership = (
                db.query(UserOrganization)
                .filter(UserOrganization.user_id == current_user.id)
                .first()
            )
        else:
            try:
                org_uuid = uuid.UUID(org_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid organization ID format",
                )
            membership = (
                db.query(UserOrganization)
                .filter(
                    UserOrganization.user_id == current_user.id,
                    UserOrganization.organization_id == org_uuid,
                )
                .first()
            )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of the active organization",
            )

        if membership.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Insufficient permissions",
            )

        return membership


class PermissionChecker:
    """
    Dependency that enforces specific permissions for the active organization.
    """

    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        org_id: Optional[str] = Depends(get_active_organization_id),
        db: Session = Depends(get_db),
    ) -> UserOrganization:
        if not org_id:
            membership = (
                db.query(UserOrganization)
                .filter(UserOrganization.user_id == current_user.id)
                .first()
            )
        else:
            try:
                org_uuid = uuid.UUID(org_id)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid organization ID format",
                )
            membership = (
                db.query(UserOrganization)
                .filter(
                    UserOrganization.user_id == current_user.id,
                    UserOrganization.organization_id == org_uuid,
                )
                .first()
            )

        if not membership:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not a member of the active organization",
            )

        # Superusers bypass normal permission checks
        if current_user.is_superuser:
            return membership

        from api.models.auth import Role

        # Resolve role name
        role_name = membership.role.value if hasattr(membership.role, "value") else str(membership.role)
        db_role = db.query(Role).filter(Role.name == role_name).first()
        if not db_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: Role configuration not found",
            )

        permissions = [p.name for p in db_role.permissions]
        if self.required_permission not in permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: Missing required permission '{self.required_permission}'",
            )

        return membership


def get_service_context(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> "ServiceContext":
    """
    Dependency that constructs a ServiceContext for the current request.
    """
    from api.services.base import ServiceContext

    # Resolve organization_id from header if present
    org_id_str = request.headers.get("x-organization-id")
    org_uuid = None
    if org_id_str:
        try:
            org_uuid = uuid.UUID(org_id_str)
        except ValueError:
            pass
            
    # If no header, maybe find first organization of user
    if not org_uuid and current_user:
        user_org = db.query(UserOrganization).filter(UserOrganization.user_id == current_user.id).first()
        if user_org:
            org_uuid = user_org.organization_id

    # Resolve roles & permissions
    roles = []
    permissions = set()
    if org_uuid and current_user:
        user_roles = db.query(UserOrganization).filter(
            UserOrganization.user_id == current_user.id,
            UserOrganization.organization_id == org_uuid,
        ).all()
        for ur in user_roles:
            roles.append(ur.role.value if hasattr(ur.role, 'value') else str(ur.role))
            
        try:
            from api.middleware.rbac import _get_user_permissions
            permissions = _get_user_permissions(current_user.id, org_uuid, db)
        except Exception:
            pass

    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")

    return ServiceContext(
        user_id=current_user.id,
        organization_id=org_uuid,
        roles=roles,
        permissions=permissions,
        client_ip=client_ip,
        user_agent=user_agent,
        is_super_admin=current_user.is_superuser,
    )
