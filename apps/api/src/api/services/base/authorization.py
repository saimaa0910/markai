"""
EAIMOS Authorization Module
===========================
Provides fine-grained Role-Based Access Control (RBAC), Attribute-Based Access Control (ABAC),
tenant scoping, resource ownership evaluation, and feature flag enforcement across the Service Layer.
"""

from typing import Any, List, Optional, Set, Union
import uuid

from api.services.base.permissions import DEFAULT_ROLE_PERMISSIONS
from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import ForbiddenOperation, UnauthorizedOperation


class AuthorizationService:
    """
    Central authorization engine enforcing tenant separation, ownership, role matrix, and permissions.
    """

    def __init__(self, role_permissions: Optional[dict[str, Set[str]]] = None) -> None:
        self.role_permissions = role_permissions or DEFAULT_ROLE_PERMISSIONS

    def check_authenticated(self, ctx: ServiceContext) -> bool:
        """Check if user identity is present in context."""
        return ctx.user_id is not None

    def require_authenticated(self, ctx: ServiceContext) -> None:
        """Enforce identity presence; raise UnauthorizedOperation if absent."""
        if not self.check_authenticated(ctx):
            raise UnauthorizedOperation(message="Authentication context required for this operation.")

    def check_permission(self, ctx: ServiceContext, permission: str) -> bool:
        """Evaluate if context satisfies required permission."""
        if ctx.is_super_admin:
            return True
        if permission in ctx.permissions or "*:*" in ctx.permissions:
            return True
        # Check permissions inherited via assigned roles
        for role in ctx.roles:
            granted = self.role_permissions.get(role, set())
            if permission in granted or "*:*" in granted:
                return True
        return False

    def require_permission(self, ctx: ServiceContext, permission: str) -> None:
        """Enforce permission; raise ForbiddenOperation if check fails."""
        self.require_authenticated(ctx)
        if not self.check_permission(ctx, permission):
            raise ForbiddenOperation(
                message=f"Missing required permission: {permission}",
                required_permissions=[permission],
            )

    def check_role(self, ctx: ServiceContext, role: str) -> bool:
        """Check if actor holds requested role."""
        if ctx.is_super_admin:
            return True
        return ctx.has_role(role)

    def require_role(self, ctx: ServiceContext, role: str) -> None:
        """Enforce role presence; raise ForbiddenOperation if absent."""
        self.require_authenticated(ctx)
        if not self.check_role(ctx, role):
            raise ForbiddenOperation(
                message=f"Actor does not possess required role: {role}",
                details={"required_role": role, "actual_roles": ctx.roles},
            )

    def check_tenant_access(self, ctx: ServiceContext, target_org_id: Union[uuid.UUID, str]) -> bool:
        """Check if actor context is authorized to access target tenant/organization."""
        return ctx.is_tenant_member(target_org_id)

    def require_tenant_access(self, ctx: ServiceContext, target_org_id: Union[uuid.UUID, str]) -> None:
        """Enforce multi-tenant organization boundary; raise ForbiddenOperation if context violates boundary."""
        self.require_authenticated(ctx)
        if not self.check_tenant_access(ctx, target_org_id):
            raise ForbiddenOperation(
                message="Tenant isolation boundary violation. Access to requested organization is prohibited.",
                details={
                    "target_organization_id": str(target_org_id),
                    "context_organization_id": ctx.get_org_id_str(),
                },
            )

    def check_ownership(
        self,
        ctx: ServiceContext,
        resource_owner_id: Optional[Union[uuid.UUID, str]],
        allow_admin_override: bool = True,
    ) -> bool:
        """Check if context user matches resource owner ID."""
        if ctx.is_super_admin and allow_admin_override:
            return True
        if not ctx.user_id or not resource_owner_id:
            return False
        return str(ctx.user_id) == str(resource_owner_id)

    def require_ownership(
        self,
        ctx: ServiceContext,
        resource_owner_id: Optional[Union[uuid.UUID, str]],
        allow_admin_override: bool = True,
    ) -> None:
        """Enforce resource ownership; raise ForbiddenOperation if context user does not own resource."""
        self.require_authenticated(ctx)
        if not self.check_ownership(ctx, resource_owner_id, allow_admin_override):
            raise ForbiddenOperation(
                message="Ownership check failed. Actor is not the owner of this resource.",
                details={
                    "resource_owner_id": str(resource_owner_id) if resource_owner_id else None,
                    "actor_user_id": ctx.get_user_id_str(),
                },
            )

    def check_feature_flag(self, ctx: ServiceContext, flag_name: str, default: bool = False) -> bool:
        """Check if feature flag is active in context."""
        return ctx.has_feature_flag(flag_name, default=default)

    def require_feature_flag(self, ctx: ServiceContext, flag_name: str, default: bool = False) -> None:
        """Enforce feature flag enablement; raise ForbiddenOperation if disabled."""
        if not self.check_feature_flag(ctx, flag_name, default=default):
            raise ForbiddenOperation(
                message=f"Feature flag '{flag_name}' is disabled for this organization.",
                details={"feature_flag": flag_name},
            )
