"""
EAIMOS IAM Validators
======================
Domain-layer validation functions for Sprint 2 IAM Service Layer.
Validates business rules, state constraints, token lifecycles, role guards,
password policies, OAuth provider restrictions, and tenant boundaries.
All validators are pure functions; they raise ServiceExceptions directly.
"""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timezone
from typing import Any, List, Optional, Set

from api.services.base.service_exceptions import (
    BusinessRuleViolation,
    ConflictError,
    ForbiddenOperation,
    ValidationError,
)
from api.services.iam.constants import (
    API_KEY_MAX_PER_ORG,
    API_KEY_SUPPORTED_SCOPES,
    SECURITY_POLICY_MINIMUM_PASSWORD_LEN,
    SUPPORTED_OAUTH_PROVIDERS,
    SYSTEM_ROLE_NAMES,
)


# =============================================================================
# Session Validators
# =============================================================================

def validate_session_not_expired(expires_at: datetime, session_id: str) -> None:
    """Raise BusinessRuleViolation if the session has passed its expiry timestamp."""
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise BusinessRuleViolation(
            message=f"Session '{session_id}' has expired.",
            rule_name="SESSION_EXPIRED",
            details={"session_id": session_id, "expired_at": expires_at.isoformat()},
        )


def validate_session_not_revoked(is_revoked: bool, session_id: str) -> None:
    """Raise BusinessRuleViolation if the session is already revoked."""
    if is_revoked:
        raise BusinessRuleViolation(
            message=f"Session '{session_id}' has been revoked.",
            rule_name="SESSION_REVOKED",
            details={"session_id": session_id},
        )


def validate_max_concurrent_sessions(
    active_session_count: int,
    max_allowed: int,
    user_id: str,
) -> None:
    """
    Raise BusinessRuleViolation if user has reached their concurrent session ceiling.
    max_allowed comes from SecurityPolicy.max_concurrent_sessions.
    """
    if active_session_count >= max_allowed:
        raise BusinessRuleViolation(
            message=(
                f"User '{user_id}' has reached the maximum of {max_allowed} "
                "concurrent sessions. Revoke an existing session before creating a new one."
            ),
            rule_name="MAX_SESSIONS_EXCEEDED",
            details={
                "user_id": user_id,
                "current_count": active_session_count,
                "max_allowed": max_allowed,
            },
        )


# =============================================================================
# Refresh Token Validators
# =============================================================================

def validate_token_not_expired(expires_at: datetime, token_id: str) -> None:
    """Raise BusinessRuleViolation if a refresh or reset token has expired."""
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise BusinessRuleViolation(
            message=f"Token '{token_id}' has expired.",
            rule_name="TOKEN_EXPIRED",
            details={"token_id": token_id, "expired_at": expires_at.isoformat()},
        )


def validate_token_not_used(is_used: bool, token_id: str) -> None:
    """Raise BusinessRuleViolation if a single-use token has already been consumed."""
    if is_used:
        raise BusinessRuleViolation(
            message=f"Token '{token_id}' has already been used.",
            rule_name="TOKEN_ALREADY_USED",
            details={"token_id": token_id},
        )


def validate_token_not_revoked(is_revoked: bool, token_id: str) -> None:
    """Raise BusinessRuleViolation if a token family has been revoked due to compromise."""
    if is_revoked:
        raise BusinessRuleViolation(
            message=f"Token '{token_id}' has been revoked. Re-authentication required.",
            rule_name="TOKEN_REVOKED",
            details={"token_id": token_id},
        )


def validate_refresh_token_family_not_compromised(
    family_id: str,
    compromised_families: Set[str],
) -> None:
    """
    Raise ForbiddenOperation if the token's family_id is in the compromised set.
    This defends against token theft replay attacks.
    """
    if family_id in compromised_families:
        raise ForbiddenOperation(
            message=(
                "Security alert: a previously consumed refresh token in this family "
                "was presented. All sessions have been revoked for your protection."
            ),
            details={"family_id": family_id},
        )


# =============================================================================
# API Key Validators
# =============================================================================

def validate_api_key_scopes(requested_scopes: List[str]) -> None:
    """Raise ValidationError if any requested scopes are not in the supported scope list."""
    invalid = set(requested_scopes) - API_KEY_SUPPORTED_SCOPES
    if invalid:
        raise ValidationError(
            message=f"Invalid API key scopes: {sorted(invalid)}.",
            field_errors=[{
                "field": "scopes",
                "message": f"Scopes {sorted(invalid)} are not supported.",
                "valid_scopes": sorted(API_KEY_SUPPORTED_SCOPES),
            }],
        )


def validate_api_key_ip_allowlist(ip_address: str, allowed_ips: Optional[List[str]]) -> None:
    """
    Raise ForbiddenOperation if the request IP is not within the key's allowed CIDR ranges.
    Skips check if allowed_ips is None or empty (unrestricted).
    """
    if not allowed_ips:
        return
    try:
        request_ip = ipaddress.ip_address(ip_address)
    except ValueError:
        raise ValidationError(
            message=f"Invalid IP address format: '{ip_address}'.",
            field_errors=[{"field": "ip_address", "message": "Not a valid IPv4 or IPv6 address."}],
        )
    for cidr in allowed_ips:
        try:
            if request_ip in ipaddress.ip_network(cidr, strict=False):
                return  # Allowed
        except ValueError:
            continue  # Skip malformed CIDR entries
    raise ForbiddenOperation(
        message=f"IP '{ip_address}' is not in the allowed IP list for this API key.",
        details={"ip_address": ip_address, "allowed_ips": allowed_ips},
    )


def validate_api_key_not_expired(expires_at: Optional[datetime], key_prefix: str) -> None:
    """Raise BusinessRuleViolation if the API key has passed its optional expiry date."""
    if expires_at is None:
        return  # No expiry configured
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise BusinessRuleViolation(
            message=f"API key '{key_prefix}...' has expired.",
            rule_name="API_KEY_EXPIRED",
            details={"key_prefix": key_prefix, "expired_at": expires_at.isoformat()},
        )


def validate_api_key_active(is_active: bool, key_prefix: str) -> None:
    """Raise BusinessRuleViolation if the API key has been deactivated."""
    if not is_active:
        raise BusinessRuleViolation(
            message=f"API key '{key_prefix}...' is inactive.",
            rule_name="API_KEY_INACTIVE",
            details={"key_prefix": key_prefix},
        )


def validate_api_key_limit_not_exceeded(current_count: int, org_id: str) -> None:
    """Raise BusinessRuleViolation if org has reached the per-org API key ceiling."""
    if current_count >= API_KEY_MAX_PER_ORG:
        raise BusinessRuleViolation(
            message=(
                f"Organization '{org_id}' has reached the maximum of "
                f"{API_KEY_MAX_PER_ORG} API keys."
            ),
            rule_name="API_KEY_LIMIT_EXCEEDED",
            details={"org_id": org_id, "limit": API_KEY_MAX_PER_ORG},
        )


# =============================================================================
# Role Validators
# =============================================================================

def validate_role_not_system(is_system: bool, role_name: str, operation: str) -> None:
    """Raise ForbiddenOperation if attempting to mutate a system-defined role."""
    if is_system:
        raise ForbiddenOperation(
            message=f"System role '{role_name}' cannot be {operation}. System roles are immutable.",
            details={"role_name": role_name, "operation": operation, "is_system": True},
        )


def validate_role_name_format(name: str) -> None:
    """
    Raise ValidationError if role name contains characters outside [A-Z0-9_-].
    System role names are uppercase; custom roles follow the same convention.
    """
    pattern = re.compile(r"^[A-Z0-9_\-]+$")
    if not pattern.match(name.upper()):
        raise ValidationError(
            message=f"Role name '{name}' contains invalid characters. Use A-Z, 0-9, _ and - only.",
            field_errors=[{"field": "name", "message": "Only uppercase letters, digits, underscores, hyphens."}],
        )


def validate_role_not_assigned_to_users(assignment_count: int, role_id: str) -> None:
    """
    Raise BusinessRuleViolation if a role still has active user assignments,
    preventing accidental deletion of a role in use.
    """
    if assignment_count > 0:
        raise BusinessRuleViolation(
            message=(
                f"Role '{role_id}' cannot be deleted: it has {assignment_count} "
                "active user assignment(s). Revoke all assignments first."
            ),
            rule_name="ROLE_HAS_ACTIVE_ASSIGNMENTS",
            details={"role_id": role_id, "assignment_count": assignment_count},
        )


def validate_user_role_not_duplicate(
    existing: bool,
    user_id: str,
    role_id: str,
    org_id: str,
) -> None:
    """Raise ConflictError if the user-role-org assignment already exists."""
    if existing:
        raise ConflictError(
            message=f"User '{user_id}' already has role '{role_id}' in organization '{org_id}'.",
            error_code="ROLE_ALREADY_ASSIGNED",
        )


def validate_role_not_expired(expires_at: Optional[datetime], role_id: str, user_id: str) -> None:
    """Raise BusinessRuleViolation if a time-limited role grant has expired."""
    if expires_at is None:
        return  # Permanent grant
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise BusinessRuleViolation(
            message=f"Role '{role_id}' grant for user '{user_id}' has expired.",
            rule_name="ROLE_GRANT_EXPIRED",
            details={"role_id": role_id, "user_id": user_id, "expired_at": expires_at.isoformat()},
        )


# =============================================================================
# Invitation Validators
# =============================================================================

def validate_invitation_not_expired(expires_at: datetime, invitation_id: str) -> None:
    """Raise BusinessRuleViolation if the invitation token has passed its expiry."""
    now = datetime.now(timezone.utc)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if now > expires_at:
        raise BusinessRuleViolation(
            message=f"Invitation '{invitation_id}' has expired.",
            rule_name="INVITATION_EXPIRED",
            details={"invitation_id": invitation_id, "expired_at": expires_at.isoformat()},
        )


def validate_invitation_not_accepted(is_accepted: bool, invitation_id: str) -> None:
    """Raise BusinessRuleViolation if the invitation has already been accepted."""
    if is_accepted:
        raise BusinessRuleViolation(
            message=f"Invitation '{invitation_id}' has already been accepted.",
            rule_name="INVITATION_ALREADY_ACCEPTED",
            details={"invitation_id": invitation_id},
        )


def validate_invitation_not_rejected(is_rejected: bool, invitation_id: str) -> None:
    """Raise BusinessRuleViolation if the invitation has already been rejected."""
    if is_rejected:
        raise BusinessRuleViolation(
            message=f"Invitation '{invitation_id}' has been rejected.",
            rule_name="INVITATION_REJECTED",
            details={"invitation_id": invitation_id},
        )


def validate_no_pending_invitation(has_pending: bool, email: str, org_id: str) -> None:
    """Raise ConflictError if a pending invitation for this email+org pair already exists."""
    if has_pending:
        raise ConflictError(
            message=f"A pending invitation for '{email}' in this organization already exists.",
            error_code="DUPLICATE_INVITATION",
        )


# =============================================================================
# Security Policy Validators
# =============================================================================

def validate_password_against_policy(
    password_plaintext: str,
    min_length: int,
    require_uppercase: bool,
    require_numbers: bool,
    require_symbols: bool,
) -> List[str]:
    """
    Validate a plaintext password against organization security policy rules.
    Returns a list of violation messages (empty = valid).
    Note: This validator operates on plaintext and must ONLY be called during auth flows,
    never stored.
    """
    violations: List[str] = []

    # Platform floor
    effective_min = max(min_length, SECURITY_POLICY_MINIMUM_PASSWORD_LEN)
    if len(password_plaintext) < effective_min:
        violations.append(f"Password must be at least {effective_min} characters long.")
    if require_uppercase and not any(c.isupper() for c in password_plaintext):
        violations.append("Password must contain at least one uppercase letter.")
    if require_numbers and not any(c.isdigit() for c in password_plaintext):
        violations.append("Password must contain at least one digit.")
    if require_symbols and not any(not c.isalnum() for c in password_plaintext):
        violations.append("Password must contain at least one special character.")
    return violations


def validate_ip_within_policy_ranges(
    ip_address: str,
    allowed_ip_ranges: Optional[List[str]],
) -> bool:
    """
    Return True if the IP is within the allowed ranges or if no ranges are configured.
    Does not raise — callers decide whether to block or log.
    """
    if not allowed_ip_ranges:
        return True  # Unrestricted
    try:
        request_ip = ipaddress.ip_address(ip_address)
    except ValueError:
        return False
    for cidr in allowed_ip_ranges:
        try:
            if request_ip in ipaddress.ip_network(cidr, strict=False):
                return True
        except ValueError:
            continue
    return False


def validate_security_policy_not_looser_than_platform(
    proposed_min_length: Optional[int],
) -> None:
    """Raise BusinessRuleViolation if org tries to lower password length below platform floor."""
    if proposed_min_length is not None and proposed_min_length < SECURITY_POLICY_MINIMUM_PASSWORD_LEN:
        raise BusinessRuleViolation(
            message=(
                f"Password minimum length cannot be set below the platform floor of "
                f"{SECURITY_POLICY_MINIMUM_PASSWORD_LEN} characters."
            ),
            rule_name="SECURITY_POLICY_TOO_PERMISSIVE",
            details={"minimum_allowed": SECURITY_POLICY_MINIMUM_PASSWORD_LEN},
        )


# =============================================================================
# OAuth Validators
# =============================================================================

def validate_oauth_provider_supported(provider: str) -> None:
    """Raise ValidationError if the specified OAuth provider is not configured."""
    if provider.lower() not in SUPPORTED_OAUTH_PROVIDERS:
        raise ValidationError(
            message=f"OAuth provider '{provider}' is not supported.",
            field_errors=[{
                "field": "provider",
                "message": f"Supported providers: {sorted(SUPPORTED_OAUTH_PROVIDERS)}",
            }],
        )


def validate_oauth_account_not_already_linked(
    is_linked: bool,
    user_id: str,
    provider: str,
) -> None:
    """Raise ConflictError if user already has this OAuth provider linked."""
    if is_linked:
        raise ConflictError(
            message=f"User '{user_id}' already has a '{provider}' account linked.",
            error_code="OAUTH_ACCOUNT_ALREADY_LINKED",
        )


def validate_oauth_provider_user_not_taken(
    is_taken: bool,
    provider: str,
    provider_user_id: str,
) -> None:
    """
    Raise ConflictError if the provider_user_id is already linked to a different EAIMOS user.
    Prevents account hijacking via OAuth re-linking.
    """
    if is_taken:
        raise ConflictError(
            message=(
                f"OAuth account '{provider_user_id}' from '{provider}' is already "
                "linked to another user."
            ),
            error_code="OAUTH_PROVIDER_USER_TAKEN",
        )
