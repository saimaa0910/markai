"""
EAIMOS IAM Data Transfer Objects (DTOs)
=========================================
Complete Pydantic v2 DTO definitions for Sprint 2 IAM Service Layer.
Covers sessions, refresh tokens, password reset, API keys, roles, permissions,
user role assignments, organization invitations, security policies, and OAuth accounts.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator

from api.services.iam.constants import (
    API_KEY_MAX_NAME_LEN,
    API_KEY_MIN_NAME_LEN,
    API_KEY_SUPPORTED_SCOPES,
    INVITE_EXPIRY_HOURS,
    ROLE_DESCRIPTION_MAX_LEN,
    ROLE_NAME_MAX_LEN,
    ROLE_NAME_MIN_LEN,
    VALID_PERMISSION_ACTIONS,
    VALID_PERMISSION_SCOPES,
)


# =============================================================================
# Session DTOs
# =============================================================================

class CreateSessionDTO(BaseModel):
    """DTO for creating a new authenticated user session."""
    user_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = Field(None, max_length=45)
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = Field(None, max_length=255)
    country_code: Optional[str] = Field(None, max_length=2)
    city: Optional[str] = Field(None, max_length=100)
    ttl_minutes: int = Field(1440, ge=1, le=10080)  # 1min–7days


class SessionResponseDTO(BaseModel):
    """Full session record returned to callers."""
    id: uuid.UUID
    user_id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    expires_at: datetime
    last_active_at: datetime
    is_revoked: bool
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionSummaryDTO(BaseModel):
    """Compact session record for list views."""
    id: uuid.UUID
    user_id: uuid.UUID
    ip_address: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    last_active_at: datetime
    expires_at: datetime
    is_revoked: bool

    model_config = {"from_attributes": True}


class RevokeSessionDTO(BaseModel):
    """Payload for session revocation."""
    reason: Optional[str] = Field(
        None,
        description="logout | admin | security | timeout | password_change",
    )


class SessionListDTO(BaseModel):
    """Paginated list of sessions."""
    items: List[SessionSummaryDTO]
    total: int
    page: int
    page_size: int


# =============================================================================
# Refresh Token DTOs
# =============================================================================

class CreateRefreshTokenDTO(BaseModel):
    """DTO for issuing a new refresh token."""
    user_id: uuid.UUID
    session_id: uuid.UUID
    ttl_days: int = Field(30, ge=1, le=90)


class RefreshTokenResponseDTO(BaseModel):
    """Refresh token record (never exposes token_hash or raw token)."""
    id: uuid.UUID
    user_id: uuid.UUID
    session_id: uuid.UUID
    family_id: uuid.UUID
    expires_at: datetime
    is_used: bool
    is_revoked: bool

    model_config = {"from_attributes": True}


class RotateTokenDTO(BaseModel):
    """DTO for executing refresh token rotation."""
    raw_token: str = Field(..., min_length=20, description="Raw refresh token presented by client")
    ip_address: Optional[str] = Field(None, max_length=45)


# =============================================================================
# Password Reset DTOs
# =============================================================================

class RequestPasswordResetDTO(BaseModel):
    """Initiate password reset for a user by email."""
    email: EmailStr
    ip_address: Optional[str] = Field(None, max_length=45)


class ConsumePasswordResetDTO(BaseModel):
    """Consume a password reset token and set new password."""
    raw_token: str = Field(..., min_length=20)
    new_password_hash: str = Field(..., min_length=60, description="Argon2 / bcrypt hash of the new password")


class PasswordResetResponseDTO(BaseModel):
    """Minimal response confirming reset token was issued."""
    id: uuid.UUID
    user_id: uuid.UUID
    expires_at: datetime
    is_used: bool

    model_config = {"from_attributes": True}


# =============================================================================
# API Key DTOs
# =============================================================================

class CreateAPIKeyDTO(BaseModel):
    """DTO for creating a new organization API key."""
    name: str = Field(..., min_length=API_KEY_MIN_NAME_LEN, max_length=API_KEY_MAX_NAME_LEN)
    scopes: List[str] = Field(default_factory=list)
    allowed_ips: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    rate_limit_rpm: int = Field(60, ge=1, le=10000)
    is_test: bool = Field(False, description="Generates a test-prefixed key (mk_test_)")

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: List[str]) -> List[str]:
        invalid = set(v) - API_KEY_SUPPORTED_SCOPES
        if invalid:
            raise ValueError(f"Unsupported scopes: {invalid}. Valid: {API_KEY_SUPPORTED_SCOPES}")
        return v


class UpdateAPIKeyDTO(BaseModel):
    """DTO for updating an existing API key (non-destructive fields only)."""
    name: Optional[str] = Field(None, min_length=API_KEY_MIN_NAME_LEN, max_length=API_KEY_MAX_NAME_LEN)
    scopes: Optional[List[str]] = None
    allowed_ips: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    rate_limit_rpm: Optional[int] = Field(None, ge=1, le=10000)
    is_active: Optional[bool] = None

    @field_validator("scopes")
    @classmethod
    def validate_scopes(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        invalid = set(v) - API_KEY_SUPPORTED_SCOPES
        if invalid:
            raise ValueError(f"Unsupported scopes: {invalid}")
        return v


class APIKeyCreatedDTO(BaseModel):
    """
    Returned ONCE on API key creation.
    Contains the plaintext key — NEVER stored or retrievable after this response.
    """
    id: uuid.UUID
    name: str
    key_prefix: str
    raw_key: str = Field(..., description="Plaintext API key — shown once, store securely")
    scopes: List[str]
    expires_at: Optional[datetime] = None
    created_at: datetime


class APIKeyResponseDTO(BaseModel):
    """Standard API key response (never exposes key_hash or raw key)."""
    id: uuid.UUID
    organization_id: uuid.UUID
    user_id: uuid.UUID
    name: str
    key_prefix: str
    scopes: List[str]
    allowed_ips: Optional[List[str]] = None
    expires_at: Optional[datetime] = None
    is_active: bool
    rate_limit_rpm: int
    last_used_at: Optional[datetime] = None
    total_calls: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class APIKeySummaryDTO(BaseModel):
    """Compact API key record for list views."""
    id: uuid.UUID
    name: str
    key_prefix: str
    scopes: List[str]
    is_active: bool
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    total_calls: int

    model_config = {"from_attributes": True}


class APIKeyListDTO(BaseModel):
    """Paginated list of API key summaries."""
    items: List[APIKeySummaryDTO]
    total: int
    page: int
    page_size: int


class APIKeyFilterDTO(BaseModel):
    """Filter parameters for API key list queries."""
    is_active: Optional[bool] = None
    has_scope: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None


# =============================================================================
# Role DTOs
# =============================================================================

class CreateRoleDTO(BaseModel):
    """DTO for creating a custom organization role."""
    name: str = Field(..., min_length=ROLE_NAME_MIN_LEN, max_length=ROLE_NAME_MAX_LEN)
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=ROLE_DESCRIPTION_MAX_LEN)
    is_default: bool = False
    metadata_json: Optional[Dict[str, Any]] = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, v: str) -> str:
        return v.strip().upper()


class UpdateRoleDTO(BaseModel):
    """DTO for updating an existing custom role."""
    display_name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, max_length=ROLE_DESCRIPTION_MAX_LEN)
    is_default: Optional[bool] = None
    metadata_json: Optional[Dict[str, Any]] = None


class RoleResponseDTO(BaseModel):
    """Full role record with associated permissions."""
    id: uuid.UUID
    organization_id: Optional[uuid.UUID] = None
    name: str
    display_name: Optional[str] = None
    description: Optional[str] = None
    is_system: bool
    is_default: bool
    permissions: List["PermissionResponseDTO"] = Field(default_factory=list)
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class RoleSummaryDTO(BaseModel):
    """Compact role record for list views."""
    id: uuid.UUID
    name: str
    display_name: Optional[str] = None
    is_system: bool
    is_default: bool
    permission_count: int = 0

    model_config = {"from_attributes": True}


class RoleListDTO(BaseModel):
    """Paginated list of role summaries."""
    items: List[RoleSummaryDTO]
    total: int
    page: int
    page_size: int


# =============================================================================
# Permission DTOs
# =============================================================================

class CreatePermissionDTO(BaseModel):
    """DTO for registering a new atomic permission."""
    resource: str = Field(..., min_length=2, max_length=100)
    action: str = Field(..., min_length=2, max_length=50)
    scope: str = Field("organization", max_length=50)
    description: Optional[str] = None

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        if v not in VALID_PERMISSION_ACTIONS:
            raise ValueError(f"Invalid action '{v}'. Must be one of: {VALID_PERMISSION_ACTIONS}")
        return v

    @field_validator("scope")
    @classmethod
    def validate_scope(cls, v: str) -> str:
        if v not in VALID_PERMISSION_SCOPES:
            raise ValueError(f"Invalid scope '{v}'. Must be one of: {VALID_PERMISSION_SCOPES}")
        return v


class PermissionResponseDTO(BaseModel):
    """Full permission record."""
    id: uuid.UUID
    resource: str
    action: str
    scope: str
    description: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AssignPermissionToRoleDTO(BaseModel):
    """Assign a permission to a role via junction table."""
    permission_id: uuid.UUID


class AssignRoleDTO(BaseModel):
    """DTO for assigning a role to a user within an organization."""
    user_id: uuid.UUID
    role_id: uuid.UUID
    organization_id: uuid.UUID
    expires_at: Optional[datetime] = Field(
        None,
        description="NULL = permanent; set for time-limited role grants",
    )


class RevokeRoleDTO(BaseModel):
    """DTO for revoking a role assignment from a user."""
    user_id: uuid.UUID
    role_id: uuid.UUID
    organization_id: uuid.UUID


class UserRoleResponseDTO(BaseModel):
    """User role assignment record with nested role details."""
    id: uuid.UUID
    user_id: uuid.UUID
    role_id: uuid.UUID
    organization_id: uuid.UUID
    granted_by: Optional[uuid.UUID] = None
    expires_at: Optional[datetime] = None
    role: Optional[RoleSummaryDTO] = None

    model_config = {"from_attributes": True}


class EffectivePermissionsDTO(BaseModel):
    """Resolved permission set for a user in an organization."""
    user_id: uuid.UUID
    organization_id: uuid.UUID
    roles: List[str]
    permissions: List[str]  # e.g. ["prompts:read", "agents:execute"]
    is_super_admin: bool = False


# =============================================================================
# Invitation DTOs
# =============================================================================

class SendInvitationDTO(BaseModel):
    """DTO for sending an organization invitation email."""
    email: EmailStr
    role: str = Field("MEMBER", description="OWNER | ADMIN | MEMBER | GUEST")
    message: Optional[str] = Field(None, max_length=1000)
    expiry_hours: int = Field(INVITE_EXPIRY_HOURS, ge=1, le=168)  # max 7 days

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"OWNER", "ADMIN", "MEMBER", "GUEST"}
        if v.upper() not in allowed:
            raise ValueError(f"Invalid role '{v}'. Must be one of: {allowed}")
        return v.upper()


class AcceptInvitationDTO(BaseModel):
    """DTO for accepting an organization invitation by secure token."""
    token: str = Field(..., min_length=10)


class InvitationResponseDTO(BaseModel):
    """Full invitation record returned to API callers."""
    id: uuid.UUID
    organization_id: uuid.UUID
    invited_by: Optional[uuid.UUID] = None
    email: str
    role: str
    message: Optional[str] = None
    token: str
    is_accepted: bool
    is_rejected: bool
    accepted_at: Optional[datetime] = None
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationSummaryDTO(BaseModel):
    """Compact invitation for list views (token hidden)."""
    id: uuid.UUID
    email: str
    role: str
    is_accepted: bool
    is_rejected: bool
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}


class InvitationListDTO(BaseModel):
    """Paginated list of invitations."""
    items: List[InvitationSummaryDTO]
    total: int
    page: int
    page_size: int


class InvitationFilterDTO(BaseModel):
    """Filter parameters for invitation list queries."""
    status: Optional[str] = Field(None, description="pending | accepted | rejected | expired")
    email: Optional[str] = None
    role: Optional[str] = None


# =============================================================================
# Security Policy DTOs
# =============================================================================

class UpdateSecurityPolicyDTO(BaseModel):
    """DTO for updating an organization security policy (partial update)."""
    mfa_required: Optional[bool] = None
    allowed_mfa_methods: Optional[List[str]] = None
    password_min_length: Optional[int] = Field(None, ge=6, le=128)
    password_require_uppercase: Optional[bool] = None
    password_require_numbers: Optional[bool] = None
    password_require_symbols: Optional[bool] = None
    password_history_count: Optional[int] = Field(None, ge=0, le=24)
    session_timeout_minutes: Optional[int] = Field(None, ge=15, le=10080)
    max_concurrent_sessions: Optional[int] = Field(None, ge=1, le=50)
    max_failed_logins: Optional[int] = Field(None, ge=3, le=20)
    lockout_duration_minutes: Optional[int] = Field(None, ge=5, le=1440)
    allowed_ip_ranges: Optional[List[str]] = None
    sso_enforced: Optional[bool] = None
    api_key_max_expiry_days: Optional[int] = Field(None, ge=1, le=365)
    api_key_require_ip_restriction: Optional[bool] = None

    @field_validator("allowed_mfa_methods")
    @classmethod
    def validate_mfa_methods(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return v
        valid = {"totp", "sms", "email", "hardware_key"}
        invalid = set(v) - valid
        if invalid:
            raise ValueError(f"Invalid MFA methods: {invalid}. Valid: {valid}")
        return v


class SecurityPolicyResponseDTO(BaseModel):
    """Full security policy record for an organization."""
    id: uuid.UUID
    organization_id: uuid.UUID
    mfa_required: bool
    allowed_mfa_methods: Optional[List[str]] = None
    password_min_length: int
    password_require_uppercase: bool
    password_require_numbers: bool
    password_require_symbols: bool
    password_history_count: int
    session_timeout_minutes: int
    max_concurrent_sessions: int
    max_failed_logins: int
    lockout_duration_minutes: int
    allowed_ip_ranges: Optional[List[str]] = None
    sso_enforced: bool
    api_key_max_expiry_days: Optional[int] = None
    api_key_require_ip_restriction: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class PasswordValidationResultDTO(BaseModel):
    """Result of validating a password against an org's security policy."""
    is_valid: bool
    violations: List[str] = Field(default_factory=list)


class IPCheckResultDTO(BaseModel):
    """Result of an IP address allowlist check."""
    is_allowed: bool
    matched_range: Optional[str] = None
    ip_address: str


# =============================================================================
# OAuth Account DTOs
# =============================================================================

class LinkOAuthAccountDTO(BaseModel):
    """DTO for linking an OAuth provider account to a user."""
    provider: str = Field(..., min_length=2, max_length=50)
    provider_user_id: str = Field(..., min_length=1, max_length=255)
    access_token_encrypted: Optional[str] = None
    refresh_token_encrypted: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    provider_email: Optional[str] = None
    provider_data: Optional[Dict[str, Any]] = None


class OAuthAccountResponseDTO(BaseModel):
    """OAuth account record (never exposes token values)."""
    id: uuid.UUID
    user_id: uuid.UUID
    provider: str
    provider_user_id: str
    provider_email: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class OAuthCallbackDTO(BaseModel):
    """Payload received from OAuth provider callback."""
    provider: str
    code: str = Field(..., min_length=1, description="Authorization code from provider")
    state: str = Field(..., min_length=1, description="CSRF state token")
    redirect_uri: str


class OAuthUserInfoDTO(BaseModel):
    """Normalized user profile returned by OAuth provider."""
    provider: str
    provider_user_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    access_token_encrypted: Optional[str] = None
    refresh_token_encrypted: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None


# ─── Resolve forward references ───────────────────────────────────────────────
RoleResponseDTO.model_rebuild()
