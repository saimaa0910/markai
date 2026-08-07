"""
RBAC Routes
============
Endpoints for managing roles and permission assignments.

Endpoints:
- GET    /rbac/roles                         — list all roles
- POST   /rbac/roles                         — create custom role (admin)
- GET    /rbac/roles/{role_id}               — get role detail
- GET    /rbac/roles/{role_id}/permissions   — get role permissions
- POST   /rbac/roles/{role_id}/permissions   — add permission to role
- DELETE /rbac/roles/{role_id}/permissions/{perm_id} — remove permission
- GET    /rbac/permissions                   — list all available permissions
- POST   /rbac/users/{user_id}/roles         — assign role to user in org
- DELETE /rbac/users/{user_id}/roles/{role_id} — remove role from user
- GET    /rbac/users/{user_id}/permissions   — get user effective permissions
"""
import uuid
from datetime import datetime
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.core.deps import get_current_user
from api.database.session import get_db
from api.middleware.rbac import require_org_role
from api.models.user import User
from api.models.auth import Role, Permission
from api.models.iam import UserRole

router = APIRouter(prefix="/rbac", tags=["rbac"])


# ─── Request/Response Schemas ─────────────────────────────────────────────────

class PermissionResponse(BaseModel):
    id: uuid.UUID
    resource: str
    action: str
    scope: str
    description: Optional[str]

    class Config:
        from_attributes = True


class RoleResponse(BaseModel):
    id: uuid.UUID
    name: str
    display_name: Optional[str]
    description: Optional[str]
    is_system: bool
    is_default: bool
    organization_id: Optional[uuid.UUID]
    permission_count: int = 0

    class Config:
        from_attributes = True


class CreateRoleRequest(BaseModel):
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    permission_ids: Optional[List[uuid.UUID]] = None


class AssignRoleRequest(BaseModel):
    role_id: uuid.UUID
    organization_id: uuid.UUID
    expires_at: Optional[datetime] = None


class AddPermissionRequest(BaseModel):
    permission_id: uuid.UUID


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _serialize_role(role: Role) -> dict:
    return {
        "id": role.id,
        "name": role.name,
        "display_name": role.display_name,
        "description": role.description,
        "is_system": role.is_system,
        "is_default": role.is_default,
        "organization_id": role.organization_id,
        "permission_count": len(role.permissions) if role.permissions else 0,
    }


def _serialize_permission(perm: Permission) -> dict:
    return {
        "id": perm.id,
        "resource": getattr(perm, "resource", ""),
        "action": getattr(perm, "action", ""),
        "scope": getattr(perm, "scope", "organization"),
        "description": perm.description,
        "name": getattr(perm, "name", None),
    }


# ─── Role Routes ──────────────────────────────────────────────────────────────

@router.get("/roles")
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    organization_id: Optional[uuid.UUID] = Query(None),
    include_system: bool = Query(True),
) -> Any:
    """List all roles (system + org-specific)."""
    query = db.query(Role)
    if not include_system:
        query = query.filter(Role.is_system == False)
    if organization_id:
        query = query.filter(
            (Role.organization_id == organization_id) | (Role.organization_id == None)
        )
    roles = query.all()
    return [_serialize_role(r) for r in roles]


@router.post("/roles", status_code=status.HTTP_201_CREATED)
def create_role(
    body: CreateRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_org_role("OWNER", "ADMIN")),
) -> Any:
    """Create a custom role for an organization."""
    # Get org from header
    from api.middleware.rbac import _get_org_id_from_request
    org_id = _get_org_id_from_request(request, current_user, db)
    if not org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization context required")

    existing = db.query(Role).filter(
        Role.name == body.name,
        Role.organization_id == org_id,
    ).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Role with this name already exists")

    role = Role(
        name=body.name.upper(),
        display_name=body.display_name or body.name,
        description=body.description,
        organization_id=org_id,
        is_system=False,
        is_default=False,
    )

    if body.permission_ids:
        perms = db.query(Permission).filter(Permission.id.in_(body.permission_ids)).all()
        role.permissions = perms

    db.add(role)
    db.commit()
    db.refresh(role)

    from api.routes.auth import log_audit
    log_audit(db, current_user.id, "ROLE_CREATED", request, {"role_name": body.name, "org_id": str(org_id)})

    return _serialize_role(role)


@router.get("/roles/{role_id}")
def get_role(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get a single role by ID."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return _serialize_role(role)


@router.get("/roles/{role_id}/permissions")
def get_role_permissions(
    role_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get all permissions for a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return [_serialize_permission(p) for p in role.permissions]


@router.post("/roles/{role_id}/permissions", status_code=status.HTTP_200_OK)
def add_permission_to_role(
    role_id: uuid.UUID,
    body: AddPermissionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_org_role("OWNER", "ADMIN")),
) -> Any:
    """Add a permission to a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify system roles")

    perm = db.query(Permission).filter(Permission.id == body.permission_id).first()
    if not perm:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Permission not found")

    if perm not in role.permissions:
        role.permissions.append(perm)
        db.commit()

    from api.routes.auth import log_audit
    log_audit(db, current_user.id, "ROLE_PERMISSION_ADDED", request, {
        "role_id": str(role_id), "permission_id": str(body.permission_id)
    })
    return {"success": True, "message": "Permission added to role"}


@router.delete("/roles/{role_id}/permissions/{perm_id}", status_code=status.HTTP_200_OK)
def remove_permission_from_role(
    role_id: uuid.UUID,
    perm_id: uuid.UUID,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_org_role("OWNER", "ADMIN")),
) -> Any:
    """Remove a permission from a role."""
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    if role.is_system:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot modify system roles")

    role.permissions = [p for p in role.permissions if p.id != perm_id]
    db.commit()

    from api.routes.auth import log_audit
    log_audit(db, current_user.id, "ROLE_PERMISSION_REMOVED", request, {
        "role_id": str(role_id), "permission_id": str(perm_id)
    })
    return {"success": True, "message": "Permission removed from role"}


# ─── Permissions ──────────────────────────────────────────────────────────────

@router.get("/permissions")
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    resource: Optional[str] = Query(None),
) -> Any:
    """List all available permissions."""
    query = db.query(Permission)
    if resource:
        if hasattr(Permission, "resource"):
            query = query.filter(Permission.resource == resource)
    perms = query.all()
    return [_serialize_permission(p) for p in perms]


# ─── User Role Assignment ─────────────────────────────────────────────────────

@router.post("/users/{user_id}/roles", status_code=status.HTTP_201_CREATED)
def assign_role_to_user(
    user_id: uuid.UUID,
    body: AssignRoleRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_org_role("OWNER", "ADMIN")),
) -> Any:
    """Assign a role to a user in an organization."""
    from api.models.user import User as UserModel

    target_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = db.query(Role).filter(Role.id == body.role_id).first()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")

    # Check if already assigned
    existing = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == body.role_id,
        UserRole.organization_id == body.organization_id,
    ).first()

    if existing:
        # Update expiry if provided
        if body.expires_at:
            existing.expires_at = body.expires_at
            db.commit()
        return {"success": True, "message": "Role already assigned (expiry updated if provided)"}

    user_role = UserRole(
        user_id=user_id,
        role_id=body.role_id,
        organization_id=body.organization_id,
        granted_by=current_user.id,
        expires_at=body.expires_at,
    )
    db.add(user_role)
    db.commit()

    from api.routes.auth import log_audit
    log_audit(db, current_user.id, "ROLE_ASSIGNED", request, {
        "target_user_id": str(user_id),
        "role_id": str(body.role_id),
        "org_id": str(body.organization_id),
    })

    # Send email notification to target user
    try:
        from api.services.email_service import send_role_changed_email
        from api.models.organization import Organization
        org = db.query(Organization).filter(Organization.id == body.organization_id).first()
        send_role_changed_email(
            target_user.email,
            target_user.full_name,
            org.name if org else "your organization",
            role.display_name or role.name,
        )
    except Exception:
        pass

    return {"success": True, "message": f"Role '{role.name}' assigned to user"}


@router.delete("/users/{user_id}/roles/{role_id}", status_code=status.HTTP_200_OK)
def remove_role_from_user(
    user_id: uuid.UUID,
    role_id: uuid.UUID,
    request: Request,
    organization_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    _: None = Depends(require_org_role("OWNER", "ADMIN")),
) -> Any:
    """Remove a role assignment from a user."""
    query = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.role_id == role_id,
    )
    if organization_id:
        query = query.filter(UserRole.organization_id == organization_id)

    user_role = query.first()
    if not user_role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role assignment not found")

    db.delete(user_role)
    db.commit()

    from api.routes.auth import log_audit
    log_audit(db, current_user.id, "ROLE_REMOVED", request, {
        "target_user_id": str(user_id),
        "role_id": str(role_id),
    })
    return {"success": True, "message": "Role removed from user"}


@router.get("/users/{user_id}/permissions")
def get_user_effective_permissions(
    user_id: uuid.UUID,
    request: Request,
    organization_id: Optional[uuid.UUID] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Get effective permissions for a user in an organization."""
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    from api.middleware.rbac import _get_user_permissions, _get_org_id_from_request

    org_id = organization_id or _get_org_id_from_request(request, current_user, db)
    if not org_id:
        return {"permissions": [], "roles": []}

    permissions = _get_user_permissions(user_id, org_id, db)

    # Also get role names
    user_roles = db.query(UserRole).filter(
        UserRole.user_id == user_id,
        UserRole.organization_id == org_id,
    ).all()

    role_names = []
    for ur in user_roles:
        role = db.query(Role).filter(Role.id == ur.role_id).first()
        if role:
            role_names.append({"id": str(ur.role_id), "name": role.name, "display_name": role.display_name})

    return {
        "user_id": str(user_id),
        "organization_id": str(org_id),
        "permissions": list(permissions),
        "roles": role_names,
    }
