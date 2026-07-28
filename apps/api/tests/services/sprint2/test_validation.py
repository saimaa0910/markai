"""
Sprint 2 IAM Validation Tests
================================
Tests for all IAM domain validator functions covering business rule violations,
security constraints, state machine guards, and policy enforcement.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

from api.services.base.service_exceptions import (
    BusinessRuleViolation,
    ConflictError,
    ForbiddenOperation,
    ValidationError,
)
from api.services.iam.validators import (
    validate_api_key_active,
    validate_api_key_ip_allowlist,
    validate_api_key_limit_not_exceeded,
    validate_api_key_not_expired,
    validate_api_key_scopes,
    validate_invitation_not_accepted,
    validate_invitation_not_expired,
    validate_invitation_not_rejected,
    validate_max_concurrent_sessions,
    validate_no_pending_invitation,
    validate_oauth_account_not_already_linked,
    validate_oauth_provider_supported,
    validate_oauth_provider_user_not_taken,
    validate_password_against_policy,
    validate_refresh_token_family_not_compromised,
    validate_role_name_format,
    validate_role_not_assigned_to_users,
    validate_role_not_system,
    validate_security_policy_not_looser_than_platform,
    validate_session_not_expired,
    validate_session_not_revoked,
    validate_token_not_expired,
    validate_token_not_used,
    validate_user_role_not_duplicate,
)


# =============================================================================
# Session Validators
# =============================================================================

class TestSessionValidators:

    def test_session_not_expired_passes_for_future_expiry(self):
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        # Should not raise
        validate_session_not_expired(expires_at, "test-session-id")

    def test_session_not_expired_raises_for_past_expiry(self):
        expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        with pytest.raises(BusinessRuleViolation) as exc_info:
            validate_session_not_expired(expires_at, "test-session-id")
        assert "expired" in str(exc_info.value).lower()

    def test_session_not_expired_handles_naive_datetime(self):
        """Validator must handle timezone-naive datetimes from legacy data."""
        expires_at = datetime.utcnow() - timedelta(minutes=5)  # naive, past
        with pytest.raises(BusinessRuleViolation):
            validate_session_not_expired(expires_at, "naive-session")

    def test_session_not_revoked_passes_for_active_session(self):
        validate_session_not_revoked(is_revoked=False, session_id="active")

    def test_session_not_revoked_raises_for_revoked_session(self):
        with pytest.raises(BusinessRuleViolation) as exc_info:
            validate_session_not_revoked(is_revoked=True, session_id="revoked")
        assert "revoked" in str(exc_info.value).lower()

    def test_max_concurrent_sessions_passes_under_limit(self):
        validate_max_concurrent_sessions(
            active_session_count=3,
            max_allowed=5,
            user_id="user-001",
        )

    def test_max_concurrent_sessions_raises_at_limit(self):
        with pytest.raises(BusinessRuleViolation) as exc_info:
            validate_max_concurrent_sessions(
                active_session_count=5,
                max_allowed=5,
                user_id="user-001",
            )
        assert "maximum" in str(exc_info.value).lower()


# =============================================================================
# Token Validators
# =============================================================================

class TestTokenValidators:

    def test_token_not_expired_passes(self):
        validate_token_not_expired(
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            token_id="tok-001",
        )

    def test_token_expired_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_token_not_expired(
                expires_at=datetime.now(timezone.utc) - timedelta(minutes=1),
                token_id="tok-001",
            )

    def test_token_not_used_passes(self):
        validate_token_not_used(is_used=False, token_id="tok-001")

    def test_token_already_used_raises(self):
        with pytest.raises(BusinessRuleViolation) as exc_info:
            validate_token_not_used(is_used=True, token_id="tok-001")
        assert "already been used" in str(exc_info.value).lower()

    def test_token_family_not_compromised_passes(self):
        family_id = str(uuid.uuid4())
        other_family = str(uuid.uuid4())
        validate_refresh_token_family_not_compromised(family_id, {other_family})

    def test_token_family_compromised_raises(self):
        family_id = str(uuid.uuid4())
        with pytest.raises(ForbiddenOperation) as exc_info:
            validate_refresh_token_family_not_compromised(family_id, {family_id})
        assert "theft" in str(exc_info.value).lower() or "reuse" in str(exc_info.value).lower() or "consumed" in str(exc_info.value).lower()


# =============================================================================
# API Key Validators
# =============================================================================

class TestAPIKeyValidators:

    def test_valid_scopes_pass(self):
        validate_api_key_scopes(["prompts:read", "agents:execute"])

    def test_invalid_scope_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            validate_api_key_scopes(["nonexistent:scope"])
        assert "scopes" in str(exc_info.value).lower()

    def test_ip_allowlist_passes_matching_ip(self):
        validate_api_key_ip_allowlist("192.168.1.50", ["192.168.1.0/24"])

    def test_ip_allowlist_blocks_non_matching_ip(self):
        with pytest.raises(ForbiddenOperation):
            validate_api_key_ip_allowlist("10.0.0.1", ["192.168.1.0/24"])

    def test_ip_allowlist_unrestricted_passes_any_ip(self):
        # allowed_ips=None means unrestricted
        validate_api_key_ip_allowlist("10.0.0.1", None)
        validate_api_key_ip_allowlist("10.0.0.1", [])

    def test_invalid_ip_format_raises(self):
        with pytest.raises(ValidationError):
            validate_api_key_ip_allowlist("not-an-ip", ["192.168.1.0/24"])

    def test_api_key_not_expired_passes(self):
        validate_api_key_not_expired(
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            key_prefix="mk_live_test",
        )

    def test_api_key_expired_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_api_key_not_expired(
                expires_at=datetime.now(timezone.utc) - timedelta(days=1),
                key_prefix="mk_live_test",
            )

    def test_api_key_no_expiry_passes(self):
        validate_api_key_not_expired(expires_at=None, key_prefix="mk_live_test")

    def test_api_key_active_passes(self):
        validate_api_key_active(is_active=True, key_prefix="mk_live_test")

    def test_api_key_inactive_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_api_key_active(is_active=False, key_prefix="mk_live_test")

    def test_key_limit_under_max_passes(self):
        validate_api_key_limit_not_exceeded(current_count=49, org_id="org-001")

    def test_key_limit_at_max_raises(self):
        from api.services.iam.constants import API_KEY_MAX_PER_ORG
        with pytest.raises(BusinessRuleViolation):
            validate_api_key_limit_not_exceeded(
                current_count=API_KEY_MAX_PER_ORG,
                org_id="org-001",
            )


# =============================================================================
# Role Validators
# =============================================================================

class TestRoleValidators:

    def test_system_role_update_raises(self):
        with pytest.raises(ForbiddenOperation) as exc_info:
            validate_role_not_system(is_system=True, role_name="ADMIN", operation="updated")
        assert "ADMIN" in str(exc_info.value)
        assert "immutable" in str(exc_info.value).lower() or "system" in str(exc_info.value).lower()

    def test_custom_role_update_passes(self):
        validate_role_not_system(is_system=False, role_name="CUSTOM", operation="updated")

    def test_role_name_format_valid(self):
        validate_role_name_format("CONTENT_MANAGER")
        validate_role_name_format("custom-role")
        validate_role_name_format("ROLE123")

    def test_role_name_format_invalid(self):
        with pytest.raises(ValidationError):
            validate_role_name_format("invalid role!")

    def test_role_with_assignments_cannot_be_deleted(self):
        with pytest.raises(BusinessRuleViolation) as exc_info:
            validate_role_not_assigned_to_users(assignment_count=3, role_id="role-001")
        assert "3" in str(exc_info.value)

    def test_role_without_assignments_can_be_deleted(self):
        validate_role_not_assigned_to_users(assignment_count=0, role_id="role-001")

    def test_duplicate_user_role_raises(self):
        with pytest.raises(ConflictError):
            validate_user_role_not_duplicate(
                existing=True,
                user_id="user-001",
                role_id="role-001",
                org_id="org-001",
            )

    def test_no_duplicate_user_role_passes(self):
        validate_user_role_not_duplicate(
            existing=False,
            user_id="user-001",
            role_id="role-001",
            org_id="org-001",
        )


# =============================================================================
# Invitation Validators
# =============================================================================

class TestInvitationValidators:

    def test_invitation_not_expired_passes(self):
        validate_invitation_not_expired(
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            invitation_id="inv-001",
        )

    def test_invitation_expired_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_invitation_not_expired(
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                invitation_id="inv-001",
            )

    def test_invitation_not_accepted_passes(self):
        validate_invitation_not_accepted(is_accepted=False, invitation_id="inv-001")

    def test_invitation_already_accepted_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_invitation_not_accepted(is_accepted=True, invitation_id="inv-001")

    def test_invitation_not_rejected_passes(self):
        validate_invitation_not_rejected(is_rejected=False, invitation_id="inv-001")

    def test_invitation_already_rejected_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_invitation_not_rejected(is_rejected=True, invitation_id="inv-001")

    def test_no_pending_invitation_passes(self):
        validate_no_pending_invitation(has_pending=False, email="a@b.com", org_id="org-001")

    def test_duplicate_invitation_raises(self):
        with pytest.raises(ConflictError):
            validate_no_pending_invitation(has_pending=True, email="a@b.com", org_id="org-001")


# =============================================================================
# Security Policy Validators
# =============================================================================

class TestSecurityPolicyValidators:

    def test_valid_password_returns_no_violations(self):
        violations = validate_password_against_policy(
            password_plaintext="SecurePass123!",
            min_length=8,
            require_uppercase=True,
            require_numbers=True,
            require_symbols=True,
        )
        assert violations == []

    def test_short_password_returns_violation(self):
        violations = validate_password_against_policy(
            password_plaintext="Short",
            min_length=8,
            require_uppercase=False,
            require_numbers=False,
            require_symbols=False,
        )
        assert len(violations) > 0
        assert any("8" in v or "characters" in v.lower() for v in violations)

    def test_missing_uppercase_returns_violation(self):
        violations = validate_password_against_policy(
            password_plaintext="lowercase123",
            min_length=8,
            require_uppercase=True,
            require_numbers=False,
            require_symbols=False,
        )
        assert any("uppercase" in v.lower() for v in violations)

    def test_missing_number_returns_violation(self):
        violations = validate_password_against_policy(
            password_plaintext="AllLettersOnly",
            min_length=8,
            require_uppercase=False,
            require_numbers=True,
            require_symbols=False,
        )
        assert any("digit" in v.lower() or "number" in v.lower() for v in violations)

    def test_missing_symbol_returns_violation(self):
        violations = validate_password_against_policy(
            password_plaintext="NoSymbols123",
            min_length=8,
            require_uppercase=False,
            require_numbers=False,
            require_symbols=True,
        )
        assert any("special" in v.lower() or "symbol" in v.lower() for v in violations)

    def test_platform_floor_below_minimum_raises(self):
        with pytest.raises(BusinessRuleViolation):
            validate_security_policy_not_looser_than_platform(proposed_min_length=4)

    def test_platform_floor_at_minimum_passes(self):
        from api.services.iam.constants import SECURITY_POLICY_MINIMUM_PASSWORD_LEN
        validate_security_policy_not_looser_than_platform(
            proposed_min_length=SECURITY_POLICY_MINIMUM_PASSWORD_LEN
        )

    def test_platform_floor_none_passes(self):
        validate_security_policy_not_looser_than_platform(proposed_min_length=None)


# =============================================================================
# OAuth Validators
# =============================================================================

class TestOAuthValidators:

    def test_supported_provider_passes(self):
        validate_oauth_provider_supported("google")
        validate_oauth_provider_supported("microsoft")
        validate_oauth_provider_supported("github")

    def test_unsupported_provider_raises(self):
        with pytest.raises(ValidationError):
            validate_oauth_provider_supported("fakebook")

    def test_provider_case_insensitive_passes(self):
        # Providers are stored as lowercase, but input should be normalized
        validate_oauth_provider_supported("GOOGLE")

    def test_account_not_linked_passes(self):
        validate_oauth_account_not_already_linked(
            is_linked=False,
            user_id="user-001",
            provider="google",
        )

    def test_already_linked_raises(self):
        with pytest.raises(ConflictError):
            validate_oauth_account_not_already_linked(
                is_linked=True,
                user_id="user-001",
                provider="google",
            )

    def test_provider_user_not_taken_passes(self):
        validate_oauth_provider_user_not_taken(
            is_taken=False,
            provider="google",
            provider_user_id="uid_123",
        )

    def test_provider_user_taken_raises(self):
        with pytest.raises(ConflictError):
            validate_oauth_provider_user_not_taken(
                is_taken=True,
                provider="google",
                provider_user_id="uid_123",
            )
