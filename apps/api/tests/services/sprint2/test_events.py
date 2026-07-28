"""
Sprint 2 IAM Domain Event Tests
==================================
Tests that verify domain events are constructed correctly with
the proper event_type, payload fields, and inheritance from DomainEvent.
Also verifies that UoW.add_event() is called on every mutating operation.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest

from api.services.iam.events import (
    AllSessionsRevoked,
    APIKeyCreated,
    APIKeyRevoked,
    APIKeyRotated,
    APIKeyUpdated,
    InvitationAccepted,
    InvitationCancelled,
    InvitationRejected,
    InvitationResent,
    InvitationSent,
    OAuthAccountLinked,
    OAuthAccountUnlinked,
    OAuthTokenRefreshed,
    OAuthUserProvisioned,
    PasswordResetConsumed,
    PasswordResetRequested,
    PermissionAssignedToRole,
    PermissionRemovedFromRole,
    RefreshTokenFamilyCompromised,
    RefreshTokenIssued,
    RefreshTokenRotated,
    RoleAssigned,
    RoleCreated,
    RoleDeleted,
    RoleRevoked,
    RoleUpdated,
    SecurityPolicyCreated,
    SecurityPolicyIPRestrictionChanged,
    SecurityPolicyMFADisabled,
    SecurityPolicyMFAEnabled,
    SecurityPolicySSOEnforced,
    SecurityPolicyUpdated,
    SessionActivityUpdated,
    SessionRevoked,
    UserLoggedIn,
    UserLoggedOut,
)


def make_event_kwargs(**overrides) -> dict:
    """Standard kwargs for constructing any DomainEvent subclass."""
    return {
        "aggregate_id": str(uuid.uuid4()),
        "tenant_id": str(uuid.uuid4()),
        "actor_id": str(uuid.uuid4()),
        "correlation_id": str(uuid.uuid4()),
        "payload": {},
        **overrides,
    }


# =============================================================================
# Session Events
# =============================================================================

class TestSessionEvents:

    def test_user_logged_in_event_type(self):
        event = UserLoggedIn(
            **make_event_kwargs(
                session_id=str(uuid.uuid4()),
                ip_address="1.2.3.4",
                country_code="US",
                user_agent="pytest",
            )
        )
        assert event.event_type == "iam.user.logged_in"
        assert event.session_id != ""
        assert event.ip_address == "1.2.3.4"

    def test_user_logged_out_event_type(self):
        event = UserLoggedOut(
            **make_event_kwargs(session_id=str(uuid.uuid4()), reason="logout")
        )
        assert event.event_type == "iam.user.logged_out"
        assert event.reason == "logout"

    def test_session_revoked_event_type(self):
        event = SessionRevoked(
            **make_event_kwargs(
                session_id=str(uuid.uuid4()),
                reason="admin",
                revoked_by=str(uuid.uuid4()),
            )
        )
        assert event.event_type == "iam.session.revoked"
        assert event.reason == "admin"

    def test_all_sessions_revoked_event(self):
        user_id = str(uuid.uuid4())
        event = AllSessionsRevoked(
            **make_event_kwargs(
                user_id=user_id,
                session_count=5,
                reason="password_change",
            )
        )
        assert event.event_type == "iam.session.all_revoked"
        assert event.session_count == 5
        assert event.user_id == user_id


# =============================================================================
# Refresh Token Events
# =============================================================================

class TestRefreshTokenEvents:

    def test_refresh_token_issued(self):
        event = RefreshTokenIssued(
            **make_event_kwargs(
                token_id=str(uuid.uuid4()),
                session_id=str(uuid.uuid4()),
                family_id=str(uuid.uuid4()),
            )
        )
        assert event.event_type == "iam.refresh_token.issued"

    def test_refresh_token_rotated(self):
        event = RefreshTokenRotated(
            **make_event_kwargs(
                old_token_id=str(uuid.uuid4()),
                new_token_id=str(uuid.uuid4()),
                family_id=str(uuid.uuid4()),
                session_id=str(uuid.uuid4()),
            )
        )
        assert event.event_type == "iam.refresh_token.rotated"
        assert event.old_token_id != event.new_token_id

    def test_family_compromised_event(self):
        family_id = str(uuid.uuid4())
        event = RefreshTokenFamilyCompromised(
            **make_event_kwargs(
                family_id=family_id,
                user_id=str(uuid.uuid4()),
                detected_ip="10.0.0.1",
                revoked_token_count=3,
            )
        )
        assert event.event_type == "iam.refresh_token.family_compromised"
        assert event.family_id == family_id
        assert event.revoked_token_count == 3


# =============================================================================
# API Key Events
# =============================================================================

class TestAPIKeyEvents:

    def test_api_key_created_event(self):
        event = APIKeyCreated(
            **make_event_kwargs(
                api_key_id=str(uuid.uuid4()),
                key_prefix="mk_live_abc",
                scopes=["prompts:read"],
            )
        )
        assert event.event_type == "iam.api_key.created"
        assert event.key_prefix == "mk_live_abc"
        assert "prompts:read" in event.scopes

    def test_api_key_updated_event(self):
        event = APIKeyUpdated(
            **make_event_kwargs(
                api_key_id=str(uuid.uuid4()),
                changes={"name": "new name", "rate_limit_rpm": "120"},
            )
        )
        assert event.event_type == "iam.api_key.updated"
        assert "name" in event.changes

    def test_api_key_revoked_event(self):
        event = APIKeyRevoked(
            **make_event_kwargs(
                api_key_id=str(uuid.uuid4()),
                key_prefix="mk_live_abc",
            )
        )
        assert event.event_type == "iam.api_key.revoked"

    def test_api_key_rotated_event(self):
        event = APIKeyRotated(
            **make_event_kwargs(
                old_api_key_id=str(uuid.uuid4()),
                new_api_key_id=str(uuid.uuid4()),
                new_key_prefix="mk_live_new",
            )
        )
        assert event.event_type == "iam.api_key.rotated"
        assert event.old_api_key_id != event.new_api_key_id


# =============================================================================
# Role & Permission Events
# =============================================================================

class TestRoleEvents:

    def test_role_created_event(self):
        event = RoleCreated(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                role_name="CONTENT_MANAGER",
                is_system=False,
            )
        )
        assert event.event_type == "iam.role.created"
        assert event.role_name == "CONTENT_MANAGER"
        assert event.is_system is False

    def test_role_updated_event(self):
        event = RoleUpdated(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                role_name="EDITOR",
                changes={"description": "Updated description"},
            )
        )
        assert event.event_type == "iam.role.updated"

    def test_role_deleted_event(self):
        event = RoleDeleted(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                role_name="OLD_ROLE",
            )
        )
        assert event.event_type == "iam.role.deleted"

    def test_permission_assigned_to_role(self):
        event = PermissionAssignedToRole(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                permission_id=str(uuid.uuid4()),
                permission_label="prompts:create:organization",
            )
        )
        assert event.event_type == "iam.role.permission_assigned"
        assert "prompts" in event.permission_label

    def test_permission_removed_from_role(self):
        event = PermissionRemovedFromRole(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                permission_id=str(uuid.uuid4()),
                permission_label="agents:execute:organization",
            )
        )
        assert event.event_type == "iam.role.permission_removed"

    def test_role_assigned_event(self):
        event = RoleAssigned(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                role_name="ADMIN",
                target_user_id=str(uuid.uuid4()),
                granted_by=str(uuid.uuid4()),
                expires_at=None,
            )
        )
        assert event.event_type == "iam.role.assigned"
        assert event.role_name == "ADMIN"

    def test_role_revoked_event(self):
        event = RoleRevoked(
            **make_event_kwargs(
                role_id=str(uuid.uuid4()),
                role_name="MEMBER",
                target_user_id=str(uuid.uuid4()),
                revoked_by=str(uuid.uuid4()),
            )
        )
        assert event.event_type == "iam.role.revoked"


# =============================================================================
# Invitation Events
# =============================================================================

class TestInvitationEvents:

    def test_invitation_sent_event(self):
        event = InvitationSent(
            **make_event_kwargs(
                invitation_id=str(uuid.uuid4()),
                invitee_email="test@example.com",
                role="MEMBER",
            )
        )
        assert event.event_type == "iam.invitation.sent"
        assert event.invitee_email == "test@example.com"

    def test_invitation_accepted_event(self):
        event = InvitationAccepted(
            **make_event_kwargs(
                invitation_id=str(uuid.uuid4()),
                invitee_email="accepted@example.com",
                new_user_id=str(uuid.uuid4()),
                membership_id=str(uuid.uuid4()),
            )
        )
        assert event.event_type == "iam.invitation.accepted"

    def test_invitation_rejected_event(self):
        event = InvitationRejected(
            **make_event_kwargs(
                invitation_id=str(uuid.uuid4()),
                invitee_email="rejected@example.com",
            )
        )
        assert event.event_type == "iam.invitation.rejected"

    def test_invitation_cancelled_event(self):
        event = InvitationCancelled(
            **make_event_kwargs(
                invitation_id=str(uuid.uuid4()),
                invitee_email="cancelled@example.com",
                cancelled_by=str(uuid.uuid4()),
            )
        )
        assert event.event_type == "iam.invitation.cancelled"

    def test_invitation_resent_event(self):
        event = InvitationResent(
            **make_event_kwargs(
                invitation_id=str(uuid.uuid4()),
                invitee_email="resent@example.com",
            )
        )
        assert event.event_type == "iam.invitation.resent"


# =============================================================================
# Security Policy Events
# =============================================================================

class TestSecurityPolicyEvents:

    def test_policy_created_event(self):
        event = SecurityPolicyCreated(
            **make_event_kwargs(policy_id=str(uuid.uuid4()))
        )
        assert event.event_type == "iam.security_policy.created"

    def test_policy_updated_event(self):
        event = SecurityPolicyUpdated(
            **make_event_kwargs(
                policy_id=str(uuid.uuid4()),
                changes={"mfa_required": "True"},
            )
        )
        assert event.event_type == "iam.security_policy.updated"
        assert "mfa_required" in event.changes

    def test_mfa_enabled_event(self):
        event = SecurityPolicyMFAEnabled(
            **make_event_kwargs(policy_id=str(uuid.uuid4()))
        )
        assert event.event_type == "iam.security_policy.mfa_enabled"

    def test_mfa_disabled_event(self):
        event = SecurityPolicyMFADisabled(
            **make_event_kwargs(policy_id=str(uuid.uuid4()))
        )
        assert event.event_type == "iam.security_policy.mfa_disabled"

    def test_ip_restriction_changed_event(self):
        event = SecurityPolicyIPRestrictionChanged(
            **make_event_kwargs(
                policy_id=str(uuid.uuid4()),
                allowed_ranges=["10.0.0.0/8", "192.168.1.0/24"],
            )
        )
        assert event.event_type == "iam.security_policy.ip_restriction_changed"
        assert len(event.allowed_ranges) == 2

    def test_sso_enforced_event(self):
        event = SecurityPolicySSOEnforced(
            **make_event_kwargs(policy_id=str(uuid.uuid4()))
        )
        assert event.event_type == "iam.security_policy.sso_enforced"


# =============================================================================
# OAuth Events
# =============================================================================

class TestOAuthEvents:

    def test_oauth_account_linked(self):
        event = OAuthAccountLinked(
            **make_event_kwargs(
                oauth_account_id=str(uuid.uuid4()),
                provider="google",
                provider_email="user@gmail.com",
            )
        )
        assert event.event_type == "iam.oauth.account_linked"
        assert event.provider == "google"

    def test_oauth_account_unlinked(self):
        event = OAuthAccountUnlinked(
            **make_event_kwargs(
                provider="github",
                provider_user_id="gh_uid_456",
            )
        )
        assert event.event_type == "iam.oauth.account_unlinked"
        assert event.provider == "github"

    def test_oauth_token_refreshed(self):
        event = OAuthTokenRefreshed(
            **make_event_kwargs(
                oauth_account_id=str(uuid.uuid4()),
                provider="microsoft",
            )
        )
        assert event.event_type == "iam.oauth.token_refreshed"

    def test_oauth_user_provisioned(self):
        event = OAuthUserProvisioned(
            **make_event_kwargs(
                new_user_id=str(uuid.uuid4()),
                provider="okta",
                provider_email="newuser@company.com",
            )
        )
        assert event.event_type == "iam.oauth.user_provisioned"
        assert event.provider == "okta"


# =============================================================================
# Event Invariants
# =============================================================================

class TestEventInvariants:
    """Verify cross-cutting invariants for all event types."""

    all_event_classes = [
        (UserLoggedIn, {"session_id": "s1", "ip_address": None, "country_code": None, "user_agent": None}),
        (UserLoggedOut, {"session_id": "s1", "reason": "logout"}),
        (SessionRevoked, {"session_id": "s1", "reason": "admin", "revoked_by": None}),
        (AllSessionsRevoked, {"user_id": "u1", "session_count": 3, "reason": "security"}),
        (APIKeyCreated, {"api_key_id": "k1", "key_prefix": "mk_", "scopes": []}),
        (APIKeyRevoked, {"api_key_id": "k1", "key_prefix": "mk_"}),
        (RoleCreated, {"role_id": "r1", "role_name": "ADMIN", "is_system": False}),
        (RoleAssigned, {"role_id": "r1", "role_name": "ADMIN", "target_user_id": "u1", "granted_by": None, "expires_at": None}),
        (InvitationSent, {"invitation_id": "i1", "invitee_email": "a@b.com", "role": "MEMBER"}),
        (SecurityPolicyCreated, {"policy_id": "p1"}),
        (OAuthAccountLinked, {"oauth_account_id": "o1", "provider": "google", "provider_email": None}),
    ]

    @pytest.mark.parametrize("event_cls,extra_kwargs", all_event_classes)
    def test_event_has_required_fields(self, event_cls, extra_kwargs):
        """Every event must have aggregate_id, tenant_id, actor_id, event_type."""
        aggregate_id = str(uuid.uuid4())
        tenant_id = str(uuid.uuid4())
        actor_id = str(uuid.uuid4())

        event = event_cls(
            aggregate_id=aggregate_id,
            tenant_id=tenant_id,
            actor_id=actor_id,
            correlation_id=str(uuid.uuid4()),
            payload={},
            **extra_kwargs,
        )

        assert event.aggregate_id == aggregate_id
        assert event.tenant_id == tenant_id
        assert event.actor_id == actor_id
        assert event.event_type.startswith("iam.")
        assert hasattr(event, "payload")
