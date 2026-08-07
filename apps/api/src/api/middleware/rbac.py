"""
RBAC Permission Middleware
===========================
Provides FastAPI dependency factories for permission-based access control.

Usage in routes:
    from api.middleware.rbac import require_permission

    @router.get("/agents")
    def list_agents(
        _: None = Depends(require_permission("agents", "read")),
        current_user: User = Depends(get_current_user),
        ...
    ):
        ...

Permission resolution chain:
    User → UserRole (org-scoped) → Role → role_permissions → Permission

Org context comes from:
1. X-Organization-Id request header
2. User's first active membership (fallback)

Superusers bypass all permission checks.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.models.user import User
from api.models.iam import UserRole
from api.models.membership import UserOrganization


def _get_org_id_from_request(request: Request, user: User, db: Session) -> Optional[uuid.UUID]:
    """Resolve active organization from header or first membership."""
    header_val = request.headers.get("x-organization-id")
    if header_val:
        try:
            return uuid.UUID(header_val)
        except ValueError:
            pass

    # Fallback: first active membership
    m = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.user_id == user.id,
            UserOrganization.deleted_at == None,
        )
        .first()
    )
    return m.organization_id if m else None


def _get_user_permissions(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Session,
) -> set[str]:
    """
    Resolve all permissions for a user in a given org.
    Returns set of "resource:action" strings.
    """
    from api.models.iam import UserRole as UserRoleModel, role_permissions_junction
    from api.models.auth import Role, Permission

    # Get all role IDs for this user in this org
    user_roles = (
        db.query(UserRoleModel)
        .filter(
            UserRoleModel.user_id == user_id,
            UserRoleModel.organization_id == org_id,
        )
        .all()
    )

    # Filter out expired roles
    now = datetime.now(timezone.utc)
    active_role_ids = [
        ur.role_id for ur in user_roles
        if not ur.expires_at or (
            ur.expires_at.replace(tzinfo=timezone.utc) if ur.expires_at.tzinfo is None
            else ur.expires_at
        ) > now
    ]

    if not active_role_ids:
        return set()

    # Get all permissions for these roles
    roles = db.query(Role).filter(Role.id.in_(active_role_ids)).all()
    permissions: set[str] = set()
    for role in roles:
        for perm in role.permissions:
            # Support both legacy string names and resource:action:scope format
            if hasattr(perm, "resource") and hasattr(perm, "action"):
                permissions.add(f"{perm.resource}:{perm.action}")
                permissions.add(f"{perm.resource}:{perm.action}:{perm.scope}")
            if hasattr(perm, "name") and perm.name:
                permissions.add(perm.name)
    return permissions


def _get_membership_role(
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    db: Session,
) -> Optional[str]:
    """Get simple membership role string (OWNER/ADMIN/MEMBER/GUEST)."""
    m = (
        db.query(UserOrganization)
        .filter(
            UserOrganization.user_id == user_id,
            UserOrganization.organization_id == org_id,
            UserOrganization.deleted_at == None,
        )
        .first()
    )
    if not m:
        return None
    return m.role.value if hasattr(m.role, "value") else str(m.role)


def require_permission(resource: str, action: str, scope: str = "organization"):
    """
    FastAPI dependency factory.

    Creates a dependency that validates the current user has the given permission
    in the active organization.

    Args:
        resource: e.g. "agents", "users", "billing", "campaigns"
        action: e.g. "read", "create", "update", "delete", "execute"
        scope: e.g. "organization", "own", "global"

    Superusers always pass. OWNERs and ADMINs get elevated access.
    """
    def _check(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        # Superusers bypass all checks
        if current_user.is_superuser:
            return

        # Check if account is pending deletion
        if current_user.deletion_requested_at and not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated pending deletion",
            )

        org_id = _get_org_id_from_request(request, current_user, db)
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active organization context. Set X-Organization-Id header.",
            )

        # Check membership
        membership_role = _get_membership_role(current_user.id, org_id, db)
        if not membership_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not a member of this organization",
            )

        # OWNERs and ADMINs get broad access (they can check specific permissions for fine-grained)
        if membership_role in ("OWNER", "ADMIN"):
            return

        # Resolve IAM permissions (from user_roles → role_permissions)
        permissions = _get_user_permissions(current_user.id, org_id, db)

        # Check if required permission is granted
        required = f"{resource}:{action}"
        required_scoped = f"{resource}:{action}:{scope}"

        if required not in permissions and required_scoped not in permissions:
            # Also check legacy-style permission names (manage_users, create_content, etc.)
            legacy_checks = {
                ("users", "read"): "manage_users",
                ("users", "create"): "manage_users",
                ("users", "update"): "manage_users",
                ("users", "delete"): "manage_users",
                ("billing", "read"): "manage_billing",
                ("billing", "update"): "manage_billing",
                ("analytics", "read"): "view_analytics",
                ("campaigns", "create"): "create_content",
                ("prompts", "create"): "create_content",
            }
            legacy_perm = legacy_checks.get((resource, action))
            if legacy_perm and legacy_perm in permissions:
                return

            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: requires {resource}:{action}",
            )

    return _check


def require_org_role(*allowed_roles: str):
    """
    Dependency that requires a minimum membership role.

    Usage:
        Depends(require_org_role("OWNER", "ADMIN"))
    """
    def _check(
        request: Request,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> None:
        if current_user.is_superuser:
            return

        org_id = _get_org_id_from_request(request, current_user, db)
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No active organization context",
            )

        role = _get_membership_role(current_user.id, org_id, db)
        if not role or role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires one of: {', '.join(allowed_roles)}",
            )

    return _check


def require_superuser():
    """Dependency that requires platform superuser."""
    def _check(current_user: User = Depends(get_current_user)) -> None:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Platform administrator access required",
            )
    return _check
