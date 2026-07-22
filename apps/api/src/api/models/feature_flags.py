"""
Feature Flag Models — Sprint 1 (Core Platform)
================================================
Platform-level feature toggles and per-organization overrides.

Tables:
- feature_flags              : Platform feature definitions
- organization_feature_flags : Per-tenant flag overrides

Design Rules:
- Feature flags are globally defined (no org_id on feature_flags)
- Org overrides can enable/disable flags regardless of global default
- rollout_percentage: 0–100, used for gradual rollouts
- allowed_plans: list of plan_tiers that get this feature by default
- CDC: sync to Databricks for feature adoption analytics
"""
import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Index, Integer, String, Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.organization import Organization
    from api.models.user import User


class FeatureFlag(Base):
    """
    Platform-level feature flag definition.

    Evaluation logic:
    1. Check organization_feature_flags for org-specific override
    2. If no override: check is_enabled_globally + rollout_percentage + allowed_plans
    3. Evaluate conditions (JSON rule engine, future)
    """
    __tablename__ = "feature_flags"

    __table_args__ = (
        UniqueConstraint("name", name="uq_feature_flags_name"),
        CheckConstraint(
            "rollout_percentage BETWEEN 0 AND 100",
            name="ck_feature_flags_rollout_pct",
        ),
        Index("idx_feature_flags_name", "name"),
        Index("idx_feature_flags_is_enabled", "is_enabled_globally"),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    name: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False,
        comment="Flag key (snake_case, e.g. 'ai_vision_mode')",
    )
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, comment="Human-readable label"
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="What this flag controls"
    )
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True,
        comment="Feature category (ai, billing, ui, security, ...)",
    )

    # ── Rollout Control ───────────────────────────────────────────────────────
    is_enabled_globally: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Default state for all organizations",
    )
    rollout_percentage: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Percentage (0–100) of orgs receiving this feature",
    )
    allowed_plans: Mapped[Optional[list]] = mapped_column(
        JSONB, nullable=True,
        comment="Plans that have access: [\"professional\", \"enterprise\"]",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    is_deprecated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Flagged for removal; still operational",
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict,
        comment="Extensible config (conditions, experiments, references)",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    org_overrides: Mapped[list["OrganizationFeatureFlag"]] = relationship(
        "OrganizationFeatureFlag", back_populates="feature_flag", cascade="all, delete-orphan"
    )


class OrganizationFeatureFlag(Base):
    """
    Per-organization override for a platform feature flag.

    A record here takes precedence over the global FeatureFlag state.
    Used for:
    - Granting early access to beta features
    - Disabling features for specific tenants
    - Enterprise custom enablement
    """
    __tablename__ = "organization_feature_flags"

    __table_args__ = (
        UniqueConstraint(
            "organization_id", "feature_flag_id",
            name="uq_org_feature_flag",
        ),
        Index("idx_org_feature_flags_org_id", "organization_id"),
        Index("idx_org_feature_flags_flag_id", "feature_flag_id"),
    )

    # ── Foreign Keys ──────────────────────────────────────────────────────────
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    feature_flag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("feature_flags.id", ondelete="CASCADE"),
        nullable=False,
    )
    overridden_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Superuser who applied the override",
    )

    # ── Override ──────────────────────────────────────────────────────────────
    is_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False,
        comment="Override state for this organization",
    )
    reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Reason for this override (audit trail)"
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    feature_flag: Mapped["FeatureFlag"] = relationship(
        "FeatureFlag", back_populates="org_overrides"
    )
    organization: Mapped["Organization"] = relationship("Organization")
    overrider: Mapped[Optional["User"]] = relationship("User", foreign_keys=[overridden_by])
