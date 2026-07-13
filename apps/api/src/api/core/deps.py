import uuid
from typing import List, Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from api.core.config import settings
from api.core.security import ALGORITHM
from api.database.session import get_db
from api.models.user import User
from api.models.membership import UserOrganization, UserRole

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
    return user


def get_active_organization_id(
    x_organization_id: Optional[str] = Header(None),
) -> Optional[str]:
    """
    Extract active organization from X-Organization-ID request header.
    """
    return x_organization_id


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
                org_uuid = uuid.UUID(str(org_id))
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
