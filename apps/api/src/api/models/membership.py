"""
Membership Models — Sprint 1 (Core Platform)
=============================================
Manages the many-to-many relationship between Users and Organizations.
Includes role assignment, invitation workflow, and organization settings.

Tables:
- user_organizations      : membership with role (OWNER/ADMIN/MEMBER/GUEST)
- organization_invitations : pending email invitations
- organization_settings   : per-tenant key-value configuration store

Design Rules:
- A user can belong to multiple organizations (no tenant-leakage)
- Membership is soft-deleted on revocation (keeps audit history)
- Only one active membership per (user_id, organization_id) pair
- Invitations expire after 72 hours by default
- Settings are namespaced (e.g. namespace='ai', key='default_model')
"""
import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean, DateTime, Enum, ForeignKey, Index, String, Text,
    UniqueConstraint, CheckConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base
import enum

if TYPE_CHECKING:
    from api.models.user import User
    from api.models.organization import Organization


class UserRole(str, enum.Enum):
    """Org-level roles. Permissions are resolved via user_roles → role_permissions."""
    OWNER = "OWNER"    # Full control; at least one owner required
    ADMIN = "ADMIN"    # Manage members, settings, integrations
    MEMBER = "MEMBER"  # Standard access
    GUEST = "GUEST"    # Read-only limited access


class UserOrganization(Base):
    """
    Many-to-many junction: User ↔ Organization with role.

    Constraints:
    - Only one ACTIVE membership per (user_id, organization_id)
    - Revocation = soft delete (deleted_at set), not hard delete
    """
    __tablename__ = "user_organizations"

    __table_args__ = (
        # Partial unique: only one active membership per user+org
        Index(
            "uq_user_org_active_membership",
            "user_id",
            "organization_id",
            unique=True,
            postgresql_where="deleted_at IS NULL",
        ),
        Index("idx_user_org_user_id", "user_id"),
        Index("idx_user_org_org_id", "organization_id"),
        Index("idx_user_org_composite", "organization_id", "user_id", "role"),
        CheckConstraint(
            "role IN ('OWNER','ADMIN','MEMBER','GUEST')",
            name="ck_user_org_role",
        ),
    )

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Role ──────────────────────────────────────────────────────────────────
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_type=False),
        nullable=False,
        default=UserRole.MEMBER,
        server_default="MEMBER",
    )

    # ── Membership Metadata ───────────────────────────────────────────────────
    is_primary: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = user's primary/default organization",
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Timestamp when membership became active",
    )
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="The user who sent the invitation",
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Member's department within the organization",
    )
    job_title: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True,
        comment="Member's job title (may differ from platform profile)",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    user: Mapped["User"] = relationship("User", back_populates="memberships", foreign_keys=[user_id])
    organization: Mapped["Organization"] = relationship("Organization", back_populates="memberships")
    inviter: Mapped[Optional["User"]] = relationship("User", foreign_keys=[invited_by])


class OrganizationInvitation(Base):
    """
    Pending invitation to join an organization.

    Lifecycle:
    1. Admin sends → record created, token emailed
    2. Invitee clicks link → token validated, membership created
    3. Invitee declines → is_rejected = TRUE
    4. Token expires → expires_at < NOW()

    Business Rules:
    - One active (non-accepted, non-rejected) invite per (org, email)
    - Tokens are securely random (128-bit entropy, URL-safe base64)
    - Invites expire after 72 hours (configurable via org settings)
    """
    __tablename__ = "organization_invitations"

    __table_args__ = (
        UniqueConstraint("token", name="uq_org_invitation_token"),
        # Only one PENDING invite per (org, email)
        Index(
            "uq_org_invitation_pending",
            "organization_id",
            "email",
            unique=True,
            postgresql_where="is_accepted = FALSE AND is_rejected = FALSE",
        ),
        Index("idx_org_invitations_org_id", "organization_id"),
        Index("idx_org_invitations_email", "email"),
        Index("idx_org_invitations_expires_at", "expires_at"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Invitation Details ────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Invitee email address"
    )
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum", create_type=False),
        nullable=False,
        default=UserRole.MEMBER,
        comment="Role to assign upon acceptance",
    )
    token: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False,
        comment="Secure random token (128-bit entropy, URL-safe base64)",
    )
    message: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Optional personal invite message"
    )

    # ── State ─────────────────────────────────────────────────────────────────
    is_accepted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    is_rejected: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    accepted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        comment="Invitation expires at this time (default: 72h from creation)",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    organization: Mapped["Organization"] = relationship(
        "Organization", back_populates="invitations"
    )
    inviter: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[invited_by]
    )


class OrganizationSettings(Base):
    """
    Per-organization key-value configuration store.

    Namespaced to prevent key collisions:
    - namespace='ai'        → AI gateway settings
    - namespace='billing'   → billing preferences
    - namespace='security'  → security policy overrides
    - namespace='ui'        → UI customization
    - namespace='smtp'      → custom email settings

    Encrypted values: is_encrypted=TRUE means value is AES-256-GCM encrypted at rest.
    """
    __tablename__ = "organization_settings"

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "namespace", "key",
            name="uq_org_setting_namespace_key",
        ),
        Index("idx_org_settings_org_namespace", "organization_id", "namespace"),
        Index("idx_org_settings_org_key", "organization_id", "key"),
    )

    # ── Foreign Key ───────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # ── Setting ───────────────────────────────────────────────────────────────
    namespace: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Setting group (ai, billing, security, ui, smtp, ...)",
    )
    key: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Setting key"
    )
    value: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Scalar string value"
    )
    value_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Structured value for complex settings"
    )
    data_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="string", server_default="string",
        comment="string | integer | boolean | json",
    )
    is_encrypted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="TRUE = value is AES-256-GCM encrypted at rest",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Admin documentation for this setting"
    )
