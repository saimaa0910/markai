"""
EAIMOS IAM Domain Events
=========================
Defines all domain events emitted by Sprint 2 IAM services.
Events are dispatched post-commit via UnitOfWorkService, enabling
audit logging, async processing, webhooks, and analytics pipelines.
"""

from typing import Any, Dict, List, Optional
from pydantic import Field

from api.services.base.events import DomainEvent


# =============================================================================
# Session Events
# =============================================================================

class UserLoggedIn(DomainEvent):
    """Emitted when a user successfully authenticates and a session is created."""
    event_type: str = "iam.user.logged_in"
    session_id: str = ""
    ip_address: Optional[str] = None
    country_code: Optional[str] = None
    user_agent: Optional[str] = None


class UserLoggedOut(DomainEvent):
    """Emitted when a user explicitly logs out, revoking their session."""
    event_type: str = "iam.user.logged_out"
    session_id: str = ""
    reason: str = "logout"


class SessionRevoked(DomainEvent):
    """Emitted when a single session is forcibly revoked (admin action or security event)."""
    event_type: str = "iam.session.revoked"
    session_id: str = ""
    reason: str = ""
    revoked_by: Optional[str] = None


class AllSessionsRevoked(DomainEvent):
    """Emitted when all active sessions for a user are revoked (password change, security incident)."""
    event_type: str = "iam.session.all_revoked"
    user_id: str = ""
    session_count: int = 0
    reason: str = ""


class SessionActivityUpdated(DomainEvent):
    """Emitted on session sliding window refresh (throttled; not per-request)."""
    event_type: str = "iam.session.activity_updated"
    session_id: str = ""


# =============================================================================
# Refresh Token Events
# =============================================================================

class RefreshTokenIssued(DomainEvent):
    """Emitted when a new refresh token is issued for a session."""
    event_type: str = "iam.refresh_token.issued"
    token_id: str = ""
    session_id: str = ""
    family_id: str = ""


class RefreshTokenRotated(DomainEvent):
    """Emitted on successful refresh token rotation."""
    event_type: str = "iam.refresh_token.rotated"
    old_token_id: str = ""
    new_token_id: str = ""
    family_id: str = ""
    session_id: str = ""


class RefreshTokenFamilyCompromised(DomainEvent):
    """
    Emitted when token reuse is detected, indicating potential theft.
    All tokens in the family are revoked as a security response.
    """
    event_type: str = "iam.refresh_token.family_compromised"
    family_id: str = ""
    user_id: str = ""
    detected_ip: Optional[str] = None
    revoked_token_count: int = 0


# =============================================================================
# Password Reset Events
# =============================================================================

class PasswordResetRequested(DomainEvent):
    """Emitted when a password reset token is issued for a user."""
    event_type: str = "iam.password_reset.requested"
    token_id: str = ""
    ip_address: Optional[str] = None


class PasswordResetConsumed(DomainEvent):
    """Emitted when a password reset token is successfully used."""
    event_type: str = "iam.password_reset.consumed"
    token_id: str = ""


class PasswordResetExpired(DomainEvent):
    """Emitted when a password reset token expires without being used."""
    event_type: str = "iam.password_reset.expired"
    token_id: str = ""


# =============================================================================
# API Key Events
# =============================================================================

class APIKeyCreated(DomainEvent):
    """Emitted when a new API key is issued for an organization."""
    event_type: str = "iam.api_key.created"
    api_key_id: str = ""
    key_prefix: str = ""
    scopes: List[str] = Field(default_factory=list)


class APIKeyUpdated(DomainEvent):
    """Emitted when an API key's metadata (name, scopes, limits) is changed."""
    event_type: str = "iam.api_key.updated"
    api_key_id: str = ""
    changes: Dict[str, Any] = Field(default_factory=dict)


class APIKeyRevoked(DomainEvent):
    """Emitted when an API key is soft-deleted (revoked)."""
    event_type: str = "iam.api_key.revoked"
    api_key_id: str = ""
    key_prefix: str = ""


class APIKeyRotated(DomainEvent):
    """Emitted when an API key is rotated (old revoked, new issued)."""
    event_type: str = "iam.api_key.rotated"
    old_api_key_id: str = ""
    new_api_key_id: str = ""
    new_key_prefix: str = ""


class APIKeyUsed(DomainEvent):
    """Emitted when an API key is used to authenticate a request (rate-throttled)."""
    event_type: str = "iam.api_key.used"
    api_key_id: str = ""
    ip_address: Optional[str] = None


# =============================================================================
# Role & Permission Events
# =============================================================================

class RoleCreated(DomainEvent):
    """Emitted when a new custom role is created in an organization."""
    event_type: str = "iam.role.created"
    role_id: str = ""
    role_name: str = ""
    is_system: bool = False


class RoleUpdated(DomainEvent):
    """Emitted when a role's metadata is changed."""
    event_type: str = "iam.role.updated"
    role_id: str = ""
    role_name: str = ""
    changes: Dict[str, Any] = Field(default_factory=dict)


class RoleDeleted(DomainEvent):
    """Emitted when a custom role is deleted."""
    event_type: str = "iam.role.deleted"
    role_id: str = ""
    role_name: str = ""


class PermissionAssignedToRole(DomainEvent):
    """Emitted when a permission is linked to a role."""
    event_type: str = "iam.role.permission_assigned"
    role_id: str = ""
    permission_id: str = ""
    permission_label: str = ""  # e.g. "prompts:create:organization"


class PermissionRemovedFromRole(DomainEvent):
    """Emitted when a permission is removed from a role."""
    event_type: str = "iam.role.permission_removed"
    role_id: str = ""
    permission_id: str = ""
    permission_label: str = ""


class RoleAssigned(DomainEvent):
    """Emitted when a role is granted to a user in an organization."""
    event_type: str = "iam.role.assigned"
    role_id: str = ""
    role_name: str = ""
    target_user_id: str = ""
    granted_by: Optional[str] = None
    expires_at: Optional[str] = None


class RoleRevoked(DomainEvent):
    """Emitted when a role assignment is removed from a user."""
    event_type: str = "iam.role.revoked"
    role_id: str = ""
    role_name: str = ""
    target_user_id: str = ""
    revoked_by: Optional[str] = None


# =============================================================================
# Invitation Events
# =============================================================================

class InvitationSent(DomainEvent):
    """Emitted when an organization invitation is created and dispatched."""
    event_type: str = "iam.invitation.sent"
    invitation_id: str = ""
    invitee_email: str = ""
    role: str = ""


class InvitationAccepted(DomainEvent):
    """Emitted when an invitation is accepted and membership is created."""
    event_type: str = "iam.invitation.accepted"
    invitation_id: str = ""
    invitee_email: str = ""
    new_user_id: str = ""
    membership_id: str = ""


class InvitationRejected(DomainEvent):
    """Emitted when an invitee explicitly declines an invitation."""
    event_type: str = "iam.invitation.rejected"
    invitation_id: str = ""
    invitee_email: str = ""


class InvitationCancelled(DomainEvent):
    """Emitted when an admin cancels a pending invitation."""
    event_type: str = "iam.invitation.cancelled"
    invitation_id: str = ""
    invitee_email: str = ""
    cancelled_by: Optional[str] = None


class InvitationResent(DomainEvent):
    """Emitted when a new token is issued for an existing invitation."""
    event_type: str = "iam.invitation.resent"
    invitation_id: str = ""
    invitee_email: str = ""


class InvitationExpired(DomainEvent):
    """Emitted during cleanup when an invitation passes its expiry date."""
    event_type: str = "iam.invitation.expired"
    invitation_id: str = ""
    invitee_email: str = ""


# =============================================================================
# Security Policy Events
# =============================================================================

class SecurityPolicyCreated(DomainEvent):
    """Emitted when a default security policy is auto-provisioned for a new org."""
    event_type: str = "iam.security_policy.created"
    policy_id: str = ""


class SecurityPolicyUpdated(DomainEvent):
    """Emitted when any security policy fields are changed."""
    event_type: str = "iam.security_policy.updated"
    policy_id: str = ""
    changes: Dict[str, Any] = Field(default_factory=dict)


class SecurityPolicyMFAEnabled(DomainEvent):
    """Emitted specifically when MFA enforcement is activated for an org."""
    event_type: str = "iam.security_policy.mfa_enabled"
    policy_id: str = ""


class SecurityPolicyMFADisabled(DomainEvent):
    """Emitted when MFA enforcement is deactivated."""
    event_type: str = "iam.security_policy.mfa_disabled"
    policy_id: str = ""


class SecurityPolicyIPRestrictionChanged(DomainEvent):
    """Emitted when IP allowlist rules are added or removed."""
    event_type: str = "iam.security_policy.ip_restriction_changed"
    policy_id: str = ""
    allowed_ranges: List[str] = Field(default_factory=list)


class SecurityPolicySSOEnforced(DomainEvent):
    """Emitted when SSO-only login is activated (password login disabled)."""
    event_type: str = "iam.security_policy.sso_enforced"
    policy_id: str = ""


# =============================================================================
# OAuth Events
# =============================================================================

class OAuthAccountLinked(DomainEvent):
    """Emitted when a user links an OAuth provider account."""
    event_type: str = "iam.oauth.account_linked"
    oauth_account_id: str = ""
    provider: str = ""
    provider_email: Optional[str] = None


class OAuthAccountUnlinked(DomainEvent):
    """Emitted when a user removes a linked OAuth provider account."""
    event_type: str = "iam.oauth.account_unlinked"
    provider: str = ""
    provider_user_id: str = ""


class OAuthTokenRefreshed(DomainEvent):
    """Emitted when OAuth provider tokens are refreshed and re-stored."""
    event_type: str = "iam.oauth.token_refreshed"
    oauth_account_id: str = ""
    provider: str = ""


class OAuthUserProvisioned(DomainEvent):
    """Emitted when a new user is auto-created via OAuth SSO flow."""
    event_type: str = "iam.oauth.user_provisioned"
    new_user_id: str = ""
    provider: str = ""
    provider_email: Optional[str] = None
