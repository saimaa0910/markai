"""
EAIMOS IAM Service Constants
=============================
Defines all domain-specific constants for Sprint 2 Identity & Access Management.
Covers session lifetimes, token TTLs, API key constraints, invitation windows,
OAuth providers, and security policy defaults.
"""

from typing import Dict, Any


# ─── Session ──────────────────────────────────────────────────────────────────

SESSION_TTL_MINUTES: int = 1440              # 24 hours (default idle timeout)
SESSION_EXTENDED_TTL_MINUTES: int = 10080   # 7 days (remember me)
SESSION_SLIDING_WINDOW: bool = True         # Refresh last_active_at on each request
MAX_SESSIONS_PER_USER: int = 10             # Hard platform ceiling (overridden by SecurityPolicy)


# ─── Refresh Tokens ───────────────────────────────────────────────────────────

REFRESH_TOKEN_TTL_DAYS: int = 30             # Refresh token validity period
REFRESH_TOKEN_BYTES: int = 32               # Entropy bytes for token generation


# ─── Password Reset ───────────────────────────────────────────────────────────

PASSWORD_RESET_TTL_MINUTES: int = 60         # Password reset token valid for 1 hour
PASSWORD_RESET_TOKEN_BYTES: int = 32         # Entropy bytes


# ─── API Keys ─────────────────────────────────────────────────────────────────

API_KEY_PREFIX_LIVE: str = "mk_live_"       # Production API key prefix
API_KEY_PREFIX_TEST: str = "mk_test_"       # Test API key prefix
API_KEY_PREFIX_LENGTH: int = 12             # Display prefix length (stored, not secret)
API_KEY_MAX_NAME_LEN: int = 255
API_KEY_MIN_NAME_LEN: int = 3
API_KEY_DEFAULT_RPM: int = 60               # Default rate limit: 60 req/min
API_KEY_MAX_RPM: int = 10000
API_KEY_MAX_PER_ORG: int = 50               # Max API keys per organization
API_KEY_SUPPORTED_SCOPES: frozenset = frozenset({
    "prompts:read", "prompts:write",
    "agents:read", "agents:execute",
    "campaigns:read", "campaigns:write",
    "knowledge:read", "knowledge:write",
    "workflows:read", "workflows:execute",
    "crm:read", "crm:write",
    "analytics:read",
    "integrations:read", "integrations:write",
    "billing:read",
    "admin:read",
})


# ─── Roles & Permissions ──────────────────────────────────────────────────────

SYSTEM_ROLE_NAMES: frozenset = frozenset({
    "OWNER", "ADMIN", "MEMBER", "GUEST", "VIEWER", "ANALYST",
    "DEVELOPER", "BILLING_ADMIN",
})

ROLE_NAME_MAX_LEN: int = 100
ROLE_NAME_MIN_LEN: int = 2
ROLE_DESCRIPTION_MAX_LEN: int = 1000

VALID_PERMISSION_ACTIONS: frozenset = frozenset({
    "create", "read", "update", "delete", "execute", "export", "share", "manage",
})
VALID_PERMISSION_SCOPES: frozenset = frozenset({
    "own", "team", "organization", "global",
})


# ─── Invitations ──────────────────────────────────────────────────────────────

INVITE_EXPIRY_HOURS: int = 72               # Invitation token validity (3 days)
INVITE_TOKEN_BYTES: int = 16                # 128-bit entropy (URL-safe base64)
INVITE_MAX_PER_ORG_PENDING: int = 500       # Max outstanding invites per org


# ─── OAuth ────────────────────────────────────────────────────────────────────

SUPPORTED_OAUTH_PROVIDERS: frozenset = frozenset({
    "google", "microsoft", "github", "okta", "saml", "custom",
})
OAUTH_STATE_TTL_SECONDS: int = 300          # OAuth flow state TTL (5 min)
OAUTH_ACCESS_TOKEN_TTL_BUFFER: int = 300    # Refresh buffer (5 min before expiry)


# ─── Security Policy Defaults ─────────────────────────────────────────────────

SECURITY_POLICY_DEFAULTS: Dict[str, Any] = {
    "mfa_required": False,
    "password_min_length": 8,
    "password_require_uppercase": True,
    "password_require_numbers": True,
    "password_require_symbols": False,
    "password_history_count": 5,
    "session_timeout_minutes": SESSION_TTL_MINUTES,
    "max_concurrent_sessions": 5,
    "max_failed_logins": 5,
    "lockout_duration_minutes": 30,
    "sso_enforced": False,
    "api_key_require_ip_restriction": False,
}

SECURITY_POLICY_MINIMUM_PASSWORD_LEN: int = 6   # Platform floor — orgs cannot go below
SECURITY_POLICY_MAXIMUM_SESSION_TIMEOUT: int = 10080  # 7 days ceiling


# ─── Miscellaneous ────────────────────────────────────────────────────────────

CORRELATION_ID_HEADER: str = "X-Correlation-ID"
