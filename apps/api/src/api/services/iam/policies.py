"""
EAIMOS IAM Authorization Policies
====================================
Fine-grained authorization policies for Sprint 2 IAM operations.
Each policy function evaluates AuthorizationService and ServiceContext
to enforce RBAC, ABAC, tenant isolation, resource ownership, and feature flags.
All functions either succeed silently or raise ForbiddenOperation / UnauthorizedOperation.
"""

from typing import Any, Optional, Union
import uuid

from api.services.base.authorization import AuthorizationService
from api.services.base.permissions import EnterprisePermission
from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import ForbiddenOperation


# =============================================================================
# Session Policies
# =============================================================================

class SessionPolicy:
    """Authorization rules governing user session lifecycle operations."""

    @staticmethod
    def can_create(authorizer: AuthorizationService, ctx: ServiceContext) -> None:
        """Any authenticated user may create a session (login flow)."""
        authorizer.require_authenticated(ctx)

    @staticmethod
    def can_read(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        session_user_id: Union[uuid.UUID, str],
    ) -> None:
        """User may read their own sessions; admins may read any session within the org."""
        authorizer.require_authenticated(ctx)
        if not authorizer.check_ownership(ctx, session_user_id) and \
           not authorizer.check_permission(ctx, EnterprisePermission.IAM_SESSION_MANAGE.value):
            raise ForbiddenOperation(
                message="You may only view your own sessions.",
                details={"session_owner_id": str(session_user_id)},
            )

    @staticmethod
    def can_revoke(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        session_user_id: Union[uuid.UUID, str],
    ) -> None:
        """Owner may revoke their own session; IAM session managers may revoke any."""
        authorizer.require_authenticated(ctx)
        if not authorizer.check_ownership(ctx, session_user_id) and \
           not authorizer.check_permission(ctx, EnterprisePermission.IAM_SESSION_MANAGE.value):
            raise ForbiddenOperation(
                message="You can only revoke your own sessions unless you have session management permission.",
            )

    @staticmethod
    def can_revoke_all(authorizer: AuthorizationService, ctx: ServiceContext) -> None:
        """Requires IAM_SESSION_MANAGE or super admin to revoke ALL sessions for any user."""
        authorizer.require_authenticated(ctx)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_SESSION_MANAGE.value)

    @staticmethod
    def can_list(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        target_user_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> None:
        """User may list their own sessions; session managers may list any user's sessions."""
        authorizer.require_authenticated(ctx)
        if target_user_id and not authorizer.check_ownership(ctx, target_user_id):
            authorizer.require_permission(ctx, EnterprisePermission.IAM_SESSION_MANAGE.value)


# =============================================================================
# API Key Policies
# =============================================================================

class APIKeyPolicy:
    """Authorization rules for API key lifecycle management."""

    @staticmethod
    def can_create(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """User must be an org member with write permission to create API keys."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_USER_WRITE.value)

    @staticmethod
    def can_read(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        key_owner_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Owner may read their own keys; org admins may read all org keys."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        if not authorizer.check_ownership(ctx, key_owner_id) and \
           not authorizer.check_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value):
            raise ForbiddenOperation(message="You can only view your own API keys.")

    @staticmethod
    def can_update(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        key_owner_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Owner or admin may update an API key."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        if not authorizer.check_ownership(ctx, key_owner_id) and \
           not authorizer.check_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value):
            raise ForbiddenOperation(message="You can only modify your own API keys.")

    @staticmethod
    def can_revoke(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        key_owner_id: Union[uuid.UUID, str],
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Owner or admin may revoke (soft-delete) an API key."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        if not authorizer.check_ownership(ctx, key_owner_id) and \
           not authorizer.check_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value):
            raise ForbiddenOperation(message="You can only revoke your own API keys.")

    @staticmethod
    def can_list(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Org members with read permission may list org API keys (filtered to own unless admin)."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_USER_READ.value)


# =============================================================================
# Role Policies
# =============================================================================

class RolePolicy:
    """Authorization rules for role and permission management."""

    @staticmethod
    def can_create(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Requires IAM_ROLE_MANAGE and org membership."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value)

    @staticmethod
    def can_read(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Optional[Union[uuid.UUID, str]] = None,
    ) -> None:
        """Any authenticated user may read role definitions."""
        authorizer.require_authenticated(ctx)
        if org_id:
            authorizer.require_tenant_access(ctx, org_id)

    @staticmethod
    def can_update(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Requires IAM_ROLE_MANAGE within the org."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value)

    @staticmethod
    def can_delete(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Requires IAM_ROLE_MANAGE. Cannot delete system roles (enforced in validator)."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value)

    @staticmethod
    def can_assign(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Assigning roles to users requires IAM_ROLE_MANAGE."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value)

    @staticmethod
    def can_revoke(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Revoking role assignments requires IAM_ROLE_MANAGE."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ROLE_MANAGE.value)

    @staticmethod
    def can_manage_permissions(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
    ) -> None:
        """Only super admins may create or manage the atomic permission registry."""
        authorizer.require_authenticated(ctx)
        authorizer.require_permission(ctx, EnterprisePermission.ADMIN_SYSTEM.value)


# =============================================================================
# Invitation Policies
# =============================================================================

class InvitationPolicy:
    """Authorization rules for org invitation lifecycle."""

    @staticmethod
    def can_send(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Sending invitations requires org membership and IAM_USER_WRITE."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_USER_WRITE.value)

    @staticmethod
    def can_cancel(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        invited_by: Optional[Union[uuid.UUID, str]],
    ) -> None:
        """Invitation sender or org admin may cancel a pending invitation."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        if not authorizer.check_ownership(ctx, invited_by) and \
           not authorizer.check_permission(ctx, EnterprisePermission.IAM_USER_WRITE.value):
            raise ForbiddenOperation(
                message="Only the invitation sender or an org admin can cancel this invitation.",
            )

    @staticmethod
    def can_accept(authorizer: AuthorizationService, ctx: ServiceContext) -> None:
        """Any authenticated user may accept an invitation directed at them."""
        authorizer.require_authenticated(ctx)

    @staticmethod
    def can_list(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Listing org invitations requires org membership and IAM_USER_READ."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_USER_READ.value)


# =============================================================================
# Security Policy Policies
# =============================================================================

class SecurityPolicyPolicy:
    """Authorization rules for org security policy management."""

    @staticmethod
    def can_read(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Org admins and auditors may read the security policy."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ORG_READ.value)

    @staticmethod
    def can_update(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        """Updating security policy requires IAM_ORG_WRITE and org membership."""
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ORG_WRITE.value)


# =============================================================================
# OAuth Policies
# =============================================================================

class OAuthPolicy:
    """Authorization rules for OAuth provider account linking."""

    @staticmethod
    def can_link(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        target_user_id: Union[uuid.UUID, str],
    ) -> None:
        """Users may only link OAuth accounts to their own profile."""
        authorizer.require_authenticated(ctx)
        if not authorizer.check_ownership(ctx, target_user_id, allow_admin_override=True):
            raise ForbiddenOperation(
                message="You can only link OAuth accounts to your own profile.",
            )

    @staticmethod
    def can_unlink(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        target_user_id: Union[uuid.UUID, str],
    ) -> None:
        """Users may only unlink their own OAuth accounts."""
        authorizer.require_authenticated(ctx)
        if not authorizer.check_ownership(ctx, target_user_id, allow_admin_override=True):
            raise ForbiddenOperation(
                message="You can only unlink OAuth accounts from your own profile.",
            )

    @staticmethod
    def can_list(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        target_user_id: Union[uuid.UUID, str],
    ) -> None:
        """Users may list only their own linked OAuth accounts."""
        authorizer.require_authenticated(ctx)
        if not authorizer.check_ownership(ctx, target_user_id, allow_admin_override=True):
            raise ForbiddenOperation(
                message="You can only view your own OAuth accounts.",
            )
