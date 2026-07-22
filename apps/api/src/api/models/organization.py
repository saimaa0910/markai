"""
Organization Model — Sprint 1 (Core Platform)
=============================================
Enterprise tenant boundary for EAIMOS multi-tenant SaaS.
Every tenant-owned resource references organizations.id.

Design Rules:
- Slug is globally unique (used in URL routing and API namespacing)
- plan_tier drives feature flag access via organization_feature_flags
- deleted_at = soft delete; hard purge after 90-day grace period
- version = optimistic locking (Base provides this)
- CDC: sync to Databricks bronze.organizations_raw
"""
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, Numeric, Text, JSON, CheckConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.membership import UserOrganization, OrganizationInvitation


class Organization(Base):
    """
    Tenant boundary. Every EAIMOS resource is scoped to an organization.

    Relationships (owner = Organization):
    - memberships : UserOrganization (1:M)
    - invitations : OrganizationInvitation (1:M)
    """
    __tablename__ = "organizations"

    __table_args__ = (
        CheckConstraint(
            "plan_tier IN ('free', 'starter', 'professional', 'enterprise')",
            name="ck_organizations_plan_tier",
        ),
        CheckConstraint(
            "max_members > 0",
            name="ck_organizations_max_members_positive",
        ),
        # Partial index: only non-deleted orgs are indexed for active queries
        Index("idx_organizations_slug_active", "slug", postgresql_where="deleted_at IS NULL"),
        Index("idx_organizations_plan_tier", "plan_tier"),
        Index("idx_organizations_is_active", "is_active", postgresql_where="is_active = TRUE"),
        Index("idx_organizations_created_at", "created_at"),
    )

    # ── Core Identity ─────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Display name of the organization"
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True,
        comment="URL-safe unique identifier (immutable after creation)",
    )

    # ── Plan & Limits ─────────────────────────────────────────────────────────
    plan_tier: Mapped[str] = mapped_column(
        String(50), nullable=False, default="free", server_default="free",
        comment="Subscription tier: free | starter | professional | enterprise",
    )
    max_members: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5",
        comment="Maximum seat count (enforced by membership service)",
    )
    max_ai_credits: Mapped[float] = mapped_column(
        Numeric(12, 4), nullable=False, default=100.0000, server_default="100.0000",
        comment="Monthly AI credit budget in USD",
    )
    max_storage_gb: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5, server_default="5",
        comment="Storage quota in gigabytes",
    )

    # ── Status ────────────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE",
        comment="FALSE = suspended/disabled org",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="KYB or email domain verification completed",
    )

    # ── Profile ───────────────────────────────────────────────────────────────
    billing_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Billing contact email"
    )
    logo_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Organization logo (CDN URL)"
    )
    website: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True
    )
    industry: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    employee_count: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, comment="Approximate headcount"
    )
    country_code: Mapped[Optional[str]] = mapped_column(
        String(2), nullable=True, comment="ISO 3166-1 alpha-2"
    )
    timezone: Mapped[str] = mapped_column(
        String(100), nullable=False, default="UTC", server_default="UTC",
        comment="IANA timezone (e.g. America/New_York)",
    )
    locale: Mapped[str] = mapped_column(
        String(20), nullable=False, default="en-US", server_default="en-US"
    )

    # ── Flexible Config ───────────────────────────────────────────────────────
    settings_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="{}",
        comment="Flexible org-level settings (UI preferences, integrations)",
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict, server_default="{}",
        comment="Extensible metadata (internal tagging, enrichment)",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    memberships: Mapped[List["UserOrganization"]] = relationship(
        "UserOrganization", back_populates="organization", cascade="all, delete-orphan"
    )
    invitations: Mapped[List["OrganizationInvitation"]] = relationship(
        "OrganizationInvitation", back_populates="organization", cascade="all, delete-orphan"
    )
