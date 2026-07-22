"""
IAM Models — Sprint 2 (Identity & Access Management)
======================================================
Fine-grained RBAC, session management, token lifecycle, and API key
infrastructure for EAIMOS.

Tables:
- roles                  : Named permission bundles (system + org-custom)
- permissions            : Atomic capability declarations (resource × action × scope)
- role_permissions       : Role ↔ Permission many-to-many junction
- user_roles             : User ↔ Role assignment (org-scoped, time-limited)
- user_sessions          : Active authenticated sessions (partitioned monthly)
- refresh_tokens         : Rotating tokens with family compromise detection
- password_reset_tokens  : Short-lived (1h) password reset tokens
- api_keys               : Long-lived programmatic access keys
- oauth_providers        : SSO / OAuth2 provider configurations
- oauth_accounts         : User's linked OAuth accounts
- security_policies      : Org-level security enforcement rules

Design Rules:
- Roles can be SYSTEM (platform-defined) or CUSTOM (org-defined)
- Permissions use resource × action × scope triples (not string names)
- RefreshToken family tracking enables theft detection
- API key plaintext is NEVER stored — only SHA-256 hash
- SecurityPolicy is 1:1 per organization
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Boolean, CheckConstraint, Column, DateTime, Enum, ForeignKey,
    Index, Integer, String, Table, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base
import enum

if TYPE_CHECKING:
    from api.models.user import User
    from api.models.organization import Organization


# ─── RBAC ─────────────────────────────────────────────────────────────────────

class Role(Base):
    """
    Named permission bundle.

    System roles (is_system=TRUE) are platform-defined and non-editable.
    Custom roles can be created per organization.
    Seeded system roles: OWNER, ADMIN, MEMBER, GUEST, VIEWER, ANALYST, DEVELOPER, BILLING_ADMIN
    """
    __tablename__ = "roles"

    __table_args__ = (
        # System role names are globally unique
        Index("uq_roles_system_name", "name", unique=True, postgresql_where="is_system = TRUE"),
        # Custom roles are unique per org
        UniqueConstraint("name", "organization_id", name="uq_roles_name_org"),
        Index("idx_roles_org_id", "organization_id"),
        Index("idx_roles_is_system", "is_system"),
    )

    # ── Scope ─────────────────────────────────────────────────────────────────
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="NULL = system-level role (available to all orgs)",
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Role name e.g. OWNER, ADMIN, CUSTOM_ANALYST",
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Human-readable label"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Role purpose and access level"
    )

    # ── Flags ─────────────────────────────────────────────────────────────────
    is_system: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = platform-defined, non-editable",
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = assigned automatically on org join",
    )

    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    permissions: Mapped[List["Permission"]] = relationship(
        "Permission", secondary="role_permissions_junction", back_populates="roles"
    )
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole", back_populates="role", cascade="all, delete-orphan"
    )


class Permission(Base):
    """
    Atomic capability declaration using resource × action × scope triples.

    Examples:
    - resource=prompt,   action=create, scope=organization
    - resource=agent,    action=execute, scope=own
    - resource=billing,  action=read,   scope=organization
    - resource=campaign, action=export, scope=organization
    """
    __tablename__ = "permissions"

    __table_args__ = (
        UniqueConstraint(
            "resource", "action", "scope",
            name="uq_permissions_resource_action_scope",
        ),
        Index("idx_permissions_resource", "resource"),
        Index("idx_permissions_action", "action"),
    )

    resource: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Entity type: prompt, agent, campaign, crm, billing, ...",
    )
    action: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Operation: create | read | update | delete | execute | export | share",
    )
    scope: Mapped[str] = mapped_column(
        String(50), nullable=False, default="organization",
        comment="Boundary: own | team | organization | global",
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    roles: Mapped[List[Role]] = relationship(
        "Role", secondary="role_permissions_junction", back_populates="permissions"
    )


# Junction table for Role ↔ Permission
role_permissions_junction = Table(
    "role_permissions_junction",
    Base.metadata,
    Column("role_id", UUID(as_uuid=True), ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column("permission_id", UUID(as_uuid=True), ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True),
)


class UserRole(Base):
    """
    User ↔ Role assignment, scoped to organization.
    Supports time-limited role grants (expires_at).
    """
    __tablename__ = "user_roles"

    __table_args__ = (
        UniqueConstraint(
            "user_id", "role_id", "organization_id",
            name="uq_user_role_assignment",
        ),
        Index("idx_user_roles_user_org", "user_id", "organization_id"),
        Index("idx_user_roles_role_id", "role_id"),
        Index("idx_user_roles_org_id", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    role_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("roles.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="NULL = permanent; set for time-limited role grants",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    role: Mapped[Role] = relationship("Role", back_populates="user_roles")
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id])
    granter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[granted_by])


# ─── SESSIONS ─────────────────────────────────────────────────────────────────

class UserSession(Base):
    """
    Active authenticated user session.

    Lifecycle:
    - Created on login (JWT issued, session_id = JWT jti)
    - Updated on each request (last_active_at sliding window)
    - Expires at expires_at (configurable via security_policies)
    - Revoked on logout, security event, or admin action

    Partitioned monthly by created_at.
    Expired sessions purged after 90 days.
    """
    __tablename__ = "user_sessions"

    __table_args__ = (
        Index("idx_user_sessions_user_id", "user_id"),
        Index("idx_user_sessions_org_id", "organization_id"),
        Index("idx_user_sessions_expires_at", "expires_at"),
        Index(
            "idx_user_sessions_active",
            "user_id", "is_revoked", "expires_at",
            postgresql_where="is_revoked = FALSE",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        comment="Active org context during session",
    )

    # ── Device ────────────────────────────────────────────────────────────────
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    device_fingerprint: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Hashed device characteristics"
    )

    # ── Geo ───────────────────────────────────────────────────────────────────
    country_code: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Sliding window — updated on each API call",
    )

    # ── Revocation ────────────────────────────────────────────────────────────
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    revocation_reason: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="logout | admin | security | timeout | password_change",
    )


class RefreshToken(Base):
    """
    Rotating refresh token with family-based theft detection.

    Rotation Protocol:
    1. Client presents refresh token
    2. Server validates token_hash
    3. Server issues NEW refresh token (same family_id)
    4. Old token marked is_used=TRUE, replaced_by=new token id

    Compromise Detection:
    - If a USED token is presented again → entire family is revoked
    - This detects token theft where attacker uses old token
    """
    __tablename__ = "refresh_tokens"

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_refresh_tokens_token_hash"),
        Index("idx_refresh_tokens_user_id", "user_id"),
        Index("idx_refresh_tokens_family_id", "family_id"),
        Index("idx_refresh_tokens_session_id", "session_id"),
        Index("idx_refresh_tokens_expires_at", "expires_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Token Identity ────────────────────────────────────────────────────────
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
        comment="SHA-256 of the raw token — plaintext NEVER stored",
    )
    family_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="Shared across all rotations — used for compromise detection",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = consumed in a rotation cycle",
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Revocation ────────────────────────────────────────────────────────────
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = revoked due to security event (e.g. family compromise)",
    )
    replaced_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("refresh_tokens.id", ondelete="SET NULL"),
        nullable=True,
        comment="The new token that replaced this one during rotation",
    )


class PasswordResetToken(Base):
    """
    Short-lived (1-hour) single-use password reset token.

    Security Properties:
    - 128-bit entropy (URL-safe base64 encoded)
    - SHA-256 hash stored (plaintext never persisted)
    - Single-use (is_used=TRUE after consumption)
    - IP-logged for forensics
    """
    __tablename__ = "password_reset_tokens"

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_pwd_reset_token_hash"),
        Index("idx_pwd_reset_user_id", "user_id"),
        Index("idx_pwd_reset_expires_at", "expires_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    token_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
        comment="SHA-256 of the reset token",
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="1 hour from creation",
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP of the requestor"
    )


# ─── API KEYS ─────────────────────────────────────────────────────────────────

class APIKey(Base):
    """
    Long-lived programmatic access key for headless/API clients.

    Security:
    - Plaintext key shown ONCE on creation, never stored
    - key_hash = SHA-256(raw_key) for lookup
    - key_prefix = first 8 chars for user identification in UI
    - Scopes restrict what operations the key can perform
    - Soft-delete (deleted_at) = revocation
    """
    __tablename__ = "api_keys"

    __table_args__ = (
        UniqueConstraint("key_hash", name="uq_api_keys_key_hash"),
        UniqueConstraint("organization_id", "key_prefix", name="uq_api_keys_prefix_org"),
        Index("idx_api_keys_org_id", "organization_id"),
        Index("idx_api_keys_user_id", "user_id"),
        Index(
            "idx_api_keys_active",
            "organization_id",
            postgresql_where="deleted_at IS NULL",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Owning user — key is revoked if user is deleted",
    )

    # ── Key Material ──────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Human label e.g. 'CI/CD Pipeline'"
    )
    key_prefix: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="First 8 chars for display (e.g. mk_live_x)",
    )
    key_hash: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False,
        comment="SHA-256 of the full API key — plaintext NEVER stored",
    )

    # ── Authorization ─────────────────────────────────────────────────────────
    scopes: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, default=list, server_default="[]",
        comment="Allowed scopes: [\"prompts:read\", \"agents:execute\", ...]",
    )
    allowed_ips: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True,
        comment="IP allowlist for this key (CIDR notation)",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="NULL = no expiry",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE"
    )
    rate_limit_rpm: Mapped[int] = mapped_column(
        Integer, nullable=False, default=60, server_default="60",
        comment="Max requests per minute for this key",
    )

    # ── Usage Tracking ────────────────────────────────────────────────────────
    last_used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_used_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    total_calls: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )


# ─── OAUTH ────────────────────────────────────────────────────────────────────

class OAuthProvider(Base):
    """
    Configured OAuth2 / SSO provider.

    Scope: NULL organization_id = platform SSO (Google/GitHub login).
    Org-specific = custom enterprise SSO (Okta, SAML, Azure AD).
    """
    __tablename__ = "oauth_providers"

    __table_args__ = (
        Index("idx_oauth_providers_org_id", "organization_id"),
        Index("idx_oauth_providers_provider", "provider"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="NULL = platform-level provider",
    )
    provider: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="google | microsoft | github | okta | saml | custom",
    )
    client_id: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    client_secret_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AES-256-GCM encrypted client secret"
    )
    scopes: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="Requested OAuth scopes"
    )
    redirect_uri: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    discovery_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="OIDC discovery endpoint"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE"
    )
    config_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict,
        comment="Provider-specific configuration",
    )


class OAuthAccount(Base):
    """
    User's linked OAuth account (one per provider).
    Enables single-sign-on and account linking.
    """
    __tablename__ = "oauth_accounts"

    __table_args__ = (
        UniqueConstraint(
            "provider", "provider_user_id",
            name="uq_oauth_accounts_provider_user",
        ),
        Index("idx_oauth_accounts_user_id", "user_id"),
        Index("idx_oauth_accounts_provider", "provider"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_user_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="External user ID from provider"
    )
    access_token_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AES-256-GCM encrypted access token"
    )
    refresh_token_encrypted: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="AES-256-GCM encrypted refresh token"
    )
    token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    provider_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    provider_data: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict, comment="Raw provider profile data"
    )


# ─── SECURITY POLICY ──────────────────────────────────────────────────────────

class SecurityPolicy(Base):
    """
    Organization-level security enforcement rules.

    1:1 per organization (UNIQUE on organization_id).
    Inherits platform defaults; org can tighten (not loosen) rules.
    """
    __tablename__ = "security_policies"

    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_security_policies_org"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── MFA ───────────────────────────────────────────────────────────────────
    mfa_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Force MFA for all org members",
    )
    allowed_mfa_methods: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="[\"totp\", \"sms\"] — NULL = all methods"
    )

    # ── Password Policy ───────────────────────────────────────────────────────
    password_min_length: Mapped[int] = mapped_column(
        Integer, nullable=False, default=8, server_default="8"
    )
    password_require_uppercase: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE"
    )
    password_require_numbers: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE"
    )
    password_require_symbols: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    password_history_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5",
        comment="Number of previous passwords that cannot be reused",
    )

    # ── Session ───────────────────────────────────────────────────────────────
    session_timeout_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1440, server_default="1440",
        comment="Session idle timeout (24h default)",
    )
    max_concurrent_sessions: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )

    # ── Lockout ───────────────────────────────────────────────────────────────
    max_failed_logins: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5"
    )
    lockout_duration_minutes: Mapped[int] = mapped_column(
        Integer, nullable=False, default=30, server_default="30"
    )

    # ── Network ───────────────────────────────────────────────────────────────
    allowed_ip_ranges: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True, comment="CIDR allowlist; NULL = all IPs allowed"
    )
    sso_enforced: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = only SSO login allowed (password login disabled)",
    )

    # ── API Keys ──────────────────────────────────────────────────────────────
    api_key_max_expiry_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="NULL = no forced expiry"
    )
    api_key_require_ip_restriction: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
