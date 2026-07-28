"""
Sprint 2 IAM Authorization Policy Tests
==========================================
Tests for all IAM authorization policy functions:
SessionPolicy, APIKeyPolicy, RolePolicy, InvitationPolicy,
SecurityPolicyPolicy, OAuthPolicy.
Verifies that policies enforce authentication, tenant isolation,
permission checks, and resource ownership correctly.
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest

from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import ForbiddenOperation
from api.services.iam.policies import (
    APIKeyPolicy,
    InvitationPolicy,
    OAuthPolicy,
    RolePolicy,
    SecurityPolicyPolicy,
    SessionPolicy,
)


# =============================================================================
# Fixtures
# =============================================================================

def make_ctx(is_owner: bool = False, is_admin: bool = False) -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.is_super_admin = is_admin
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer(
    has_permission: bool = True,
    is_owner: bool = True,
) -> MagicMock:
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = has_permission
    auth.check_ownership.return_value = is_owner
    return auth


def make_denying_authorizer() -> MagicMock:
    """Authorizer that raises ForbiddenOperation on require_permission."""
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.side_effect = ForbiddenOperation(
        message="Permission denied",
    )
    auth.check_permission.return_value = False
    auth.check_ownership.return_value = False
    return auth


# =============================================================================
# SessionPolicy Tests
# =============================================================================

class TestSessionPolicy:

    def test_can_create_authenticated(self):
        auth = make_authorizer()
        ctx = make_ctx()
        # Should not raise
        SessionPolicy.can_create(auth, ctx)
        auth.require_authenticated.assert_called_once_with(ctx)

    def test_can_read_own_session(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        # Owner can read their own session
        SessionPolicy.can_read(auth, ctx, session_user_id=ctx.user_id)

    def test_can_read_others_session_with_permission(self):
        ctx = make_ctx()
        other_user_id = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=True)
        # Admin/manager can read any session
        SessionPolicy.can_read(auth, ctx, session_user_id=other_user_id)

    def test_can_read_others_session_without_permission_raises(self):
        ctx = make_ctx()
        other_user_id = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=False)
        with pytest.raises(ForbiddenOperation):
            SessionPolicy.can_read(auth, ctx, session_user_id=other_user_id)

    def test_can_revoke_own_session(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        SessionPolicy.can_revoke(auth, ctx, session_user_id=ctx.user_id)

    def test_can_revoke_others_session_without_permission_raises(self):
        ctx = make_ctx()
        other_user_id = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=False)
        with pytest.raises(ForbiddenOperation):
            SessionPolicy.can_revoke(auth, ctx, session_user_id=other_user_id)

    def test_can_revoke_all_requires_permission(self):
        ctx = make_ctx()
        auth = make_denying_authorizer()
        auth.require_authenticated.return_value = None  # Auth passes
        with pytest.raises(ForbiddenOperation):
            SessionPolicy.can_revoke_all(auth, ctx)


# =============================================================================
# APIKeyPolicy Tests
# =============================================================================

class TestAPIKeyPolicy:

    def test_can_create_with_permission(self):
        ctx = make_ctx()
        auth = make_authorizer()
        APIKeyPolicy.can_create(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()

    def test_can_read_own_key(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        APIKeyPolicy.can_read(auth, ctx, key_owner_id=ctx.user_id, org_id=ctx.organization_id)

    def test_can_read_others_key_requires_permission(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=True)
        # Should not raise — admin has permission
        APIKeyPolicy.can_read(auth, ctx, key_owner_id=other_user, org_id=ctx.organization_id)

    def test_can_read_others_key_without_permission_raises(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=False)
        with pytest.raises(ForbiddenOperation):
            APIKeyPolicy.can_read(auth, ctx, key_owner_id=other_user, org_id=ctx.organization_id)

    def test_can_revoke_own_key(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        APIKeyPolicy.can_revoke(auth, ctx, key_owner_id=ctx.user_id, org_id=ctx.organization_id)

    def test_can_revoke_others_key_without_permission_raises(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=False)
        with pytest.raises(ForbiddenOperation):
            APIKeyPolicy.can_revoke(auth, ctx, key_owner_id=other_user, org_id=ctx.organization_id)

    def test_can_list_requires_tenant_access(self):
        ctx = make_ctx()
        auth = make_authorizer()
        APIKeyPolicy.can_list(auth, ctx, org_id=ctx.organization_id)
        auth.require_tenant_access.assert_called_with(ctx, ctx.organization_id)


# =============================================================================
# RolePolicy Tests
# =============================================================================

class TestRolePolicy:

    def test_can_create_role_requires_permission(self):
        ctx = make_ctx()
        auth = make_authorizer()
        RolePolicy.can_create(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()

    def test_can_create_role_without_permission_raises(self):
        ctx = make_ctx()
        auth = make_denying_authorizer()
        auth.require_authenticated.return_value = None
        auth.require_tenant_access.return_value = None
        with pytest.raises(ForbiddenOperation):
            RolePolicy.can_create(auth, ctx, org_id=ctx.organization_id)

    def test_can_read_role_as_authenticated_user(self):
        ctx = make_ctx()
        auth = make_authorizer()
        RolePolicy.can_read(auth, ctx)  # Any authenticated user
        auth.require_authenticated.assert_called_once()

    def test_can_delete_role_requires_permission(self):
        ctx = make_ctx()
        auth = make_authorizer()
        RolePolicy.can_delete(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()

    def test_can_assign_requires_iam_role_manage(self):
        ctx = make_ctx()
        auth = make_authorizer()
        RolePolicy.can_assign(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()

    def test_can_manage_permissions_requires_system_admin(self):
        ctx = make_ctx()
        auth = make_authorizer()
        RolePolicy.can_manage_permissions(auth, ctx)
        auth.require_permission.assert_called()


# =============================================================================
# InvitationPolicy Tests
# =============================================================================

class TestInvitationPolicy:

    def test_can_send_requires_write_permission(self):
        ctx = make_ctx()
        auth = make_authorizer()
        InvitationPolicy.can_send(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()

    def test_can_send_without_permission_raises(self):
        ctx = make_ctx()
        auth = make_denying_authorizer()
        auth.require_authenticated.return_value = None
        auth.require_tenant_access.return_value = None
        with pytest.raises(ForbiddenOperation):
            InvitationPolicy.can_send(auth, ctx, org_id=ctx.organization_id)

    def test_can_cancel_own_invitation(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        InvitationPolicy.can_cancel(
            auth,
            ctx,
            org_id=ctx.organization_id,
            invited_by=ctx.user_id,
        )

    def test_can_cancel_others_invitation_without_permission_raises(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False, has_permission=False)
        with pytest.raises(ForbiddenOperation):
            InvitationPolicy.can_cancel(
                auth,
                ctx,
                org_id=ctx.organization_id,
                invited_by=other_user,
            )

    def test_can_accept_requires_authentication(self):
        ctx = make_ctx()
        auth = make_authorizer()
        InvitationPolicy.can_accept(auth, ctx)
        auth.require_authenticated.assert_called()

    def test_can_list_requires_read_permission(self):
        ctx = make_ctx()
        auth = make_authorizer()
        InvitationPolicy.can_list(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()


# =============================================================================
# SecurityPolicyPolicy Tests
# =============================================================================

class TestSecurityPolicyPolicy:

    def test_can_read_policy_requires_tenant_access(self):
        ctx = make_ctx()
        auth = make_authorizer()
        SecurityPolicyPolicy.can_read(auth, ctx, org_id=ctx.organization_id)
        auth.require_tenant_access.assert_called_with(ctx, ctx.organization_id)

    def test_can_update_policy_requires_write_permission(self):
        ctx = make_ctx()
        auth = make_authorizer()
        SecurityPolicyPolicy.can_update(auth, ctx, org_id=ctx.organization_id)
        auth.require_permission.assert_called()

    def test_can_update_policy_without_permission_raises(self):
        ctx = make_ctx()
        auth = make_denying_authorizer()
        auth.require_authenticated.return_value = None
        auth.require_tenant_access.return_value = None
        with pytest.raises(ForbiddenOperation):
            SecurityPolicyPolicy.can_update(auth, ctx, org_id=ctx.organization_id)


# =============================================================================
# OAuthPolicy Tests
# =============================================================================

class TestOAuthPolicy:

    def test_can_link_own_profile(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        OAuthPolicy.can_link(auth, ctx, target_user_id=ctx.user_id)

    def test_can_link_others_profile_raises(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False)
        auth.check_ownership.return_value = False
        with pytest.raises(ForbiddenOperation):
            OAuthPolicy.can_link(auth, ctx, target_user_id=other_user)

    def test_can_unlink_own_account(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        OAuthPolicy.can_unlink(auth, ctx, target_user_id=ctx.user_id)

    def test_can_unlink_others_account_raises(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False)
        auth.check_ownership.return_value = False
        with pytest.raises(ForbiddenOperation):
            OAuthPolicy.can_unlink(auth, ctx, target_user_id=other_user)

    def test_can_list_own_accounts(self):
        ctx = make_ctx()
        auth = make_authorizer(is_owner=True)
        OAuthPolicy.can_list(auth, ctx, target_user_id=ctx.user_id)

    def test_can_list_others_accounts_raises(self):
        ctx = make_ctx()
        other_user = uuid.uuid4()
        auth = make_authorizer(is_owner=False)
        auth.check_ownership.return_value = False
        with pytest.raises(ForbiddenOperation):
            OAuthPolicy.can_list(auth, ctx, target_user_id=other_user)
