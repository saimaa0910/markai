"""
EAIMOS IAM Cache Keys
======================
Defines structured cache key builders, TTL constants, and invalidation helpers
for all Sprint 2 IAM entities: sessions, API keys, roles, invitations, security policies,
and OAuth accounts.
"""

from typing import Optional, Union
import uuid


# ─── Cache Prefixes ───────────────────────────────────────────────────────────

IAM_CACHE_PREFIX: str = "iam"
SESSION_PREFIX: str = f"{IAM_CACHE_PREFIX}:session"
API_KEY_PREFIX: str = f"{IAM_CACHE_PREFIX}:apikey"
ROLE_PREFIX: str = f"{IAM_CACHE_PREFIX}:role"
PERMISSION_PREFIX: str = f"{IAM_CACHE_PREFIX}:permission"
USER_ROLES_PREFIX: str = f"{IAM_CACHE_PREFIX}:user_roles"
INVITATION_PREFIX: str = f"{IAM_CACHE_PREFIX}:invitation"
SECURITY_POLICY_PREFIX: str = f"{IAM_CACHE_PREFIX}:security_policy"
OAUTH_ACCOUNT_PREFIX: str = f"{IAM_CACHE_PREFIX}:oauth"


# ─── TTL Constants (seconds) ──────────────────────────────────────────────────

SESSION_KEY_TTL: int = 300           # 5 min — sessions change often
API_KEY_KEY_TTL: int = 600           # 10 min — API key lookups (stable data)
ROLE_KEY_TTL: int = 900              # 15 min — roles are semi-static
PERMISSION_KEY_TTL: int = 1800       # 30 min — permissions rarely change
USER_ROLES_KEY_TTL: int = 300        # 5 min — role assignments can change
INVITATION_KEY_TTL: int = 300        # 5 min
SECURITY_POLICY_KEY_TTL: int = 600   # 10 min — policy changes are rare but impactful
OAUTH_ACCOUNT_KEY_TTL: int = 600     # 10 min


# ─── Key Builders ─────────────────────────────────────────────────────────────

def session_cache_key(session_id: Union[uuid.UUID, str]) -> str:
    """Cache key for a single user session record."""
    return f"{SESSION_PREFIX}:{str(session_id)}"


def user_sessions_list_key(user_id: Union[uuid.UUID, str]) -> str:
    """Cache key for the list of active sessions for a user."""
    return f"{SESSION_PREFIX}:user:{str(user_id)}:list"


def api_key_by_id_cache_key(api_key_id: Union[uuid.UUID, str]) -> str:
    """Cache key for an API key looked up by its ID."""
    return f"{API_KEY_PREFIX}:id:{str(api_key_id)}"


def api_key_by_hash_cache_key(key_hash: str) -> str:
    """Cache key for an API key looked up by its SHA-256 hash (authentication path)."""
    return f"{API_KEY_PREFIX}:hash:{key_hash}"


def api_key_list_key(org_id: Union[uuid.UUID, str]) -> str:
    """Cache key for the org-scoped list of API keys."""
    return f"{API_KEY_PREFIX}:org:{str(org_id)}:list"


def role_cache_key(role_id: Union[uuid.UUID, str]) -> str:
    """Cache key for a single role record."""
    return f"{ROLE_PREFIX}:{str(role_id)}"


def org_roles_list_key(org_id: Union[uuid.UUID, str]) -> str:
    """Cache key for all roles in an organization (including system roles)."""
    return f"{ROLE_PREFIX}:org:{str(org_id)}:list"


def user_roles_cache_key(user_id: Union[uuid.UUID, str], org_id: Union[uuid.UUID, str]) -> str:
    """Cache key for the effective role assignments of a user within an org."""
    return f"{USER_ROLES_PREFIX}:{str(user_id)}:org:{str(org_id)}"


def user_permissions_cache_key(user_id: Union[uuid.UUID, str], org_id: Union[uuid.UUID, str]) -> str:
    """Cache key for the fully resolved permission set of a user within an org."""
    return f"{IAM_CACHE_PREFIX}:permissions:{str(user_id)}:org:{str(org_id)}"


def invitation_by_token_cache_key(token: str) -> str:
    """Cache key for an invitation looked up by its secure token."""
    return f"{INVITATION_PREFIX}:token:{token}"


def invitation_by_id_cache_key(inv_id: Union[uuid.UUID, str]) -> str:
    """Cache key for an invitation record by its primary ID."""
    return f"{INVITATION_PREFIX}:id:{str(inv_id)}"


def org_invitations_list_key(org_id: Union[uuid.UUID, str]) -> str:
    """Cache key for the list of invitations for an organization."""
    return f"{INVITATION_PREFIX}:org:{str(org_id)}:list"


def security_policy_cache_key(org_id: Union[uuid.UUID, str]) -> str:
    """Cache key for an organization's security policy record."""
    return f"{SECURITY_POLICY_PREFIX}:org:{str(org_id)}"


def oauth_account_cache_key(user_id: Union[uuid.UUID, str], provider: str) -> str:
    """Cache key for a user's linked OAuth account for a specific provider."""
    return f"{OAUTH_ACCOUNT_PREFIX}:user:{str(user_id)}:provider:{provider}"


def user_oauth_accounts_list_key(user_id: Union[uuid.UUID, str]) -> str:
    """Cache key for all linked OAuth accounts for a user."""
    return f"{OAUTH_ACCOUNT_PREFIX}:user:{str(user_id)}:list"


# ─── Invalidation Pattern Helpers ─────────────────────────────────────────────

def invalidate_pattern_for_user_sessions(user_id: Union[uuid.UUID, str]) -> str:
    """Glob pattern matching all cached session keys for a specific user."""
    return f"{SESSION_PREFIX}:user:{str(user_id)}:*"


def invalidate_pattern_for_org_roles(org_id: Union[uuid.UUID, str]) -> str:
    """Glob pattern matching all cached role-related keys for an organization."""
    return f"{ROLE_PREFIX}:org:{str(org_id)}:*"


def invalidate_pattern_for_user_permissions(user_id: Union[uuid.UUID, str]) -> str:
    """Glob pattern matching all permission cache keys for a user across all orgs."""
    return f"{IAM_CACHE_PREFIX}:permissions:{str(user_id)}:*"
