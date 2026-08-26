"""
User Model — Sprint 1 (Core Platform)
======================================
Platform-level identity for EAIMOS. Users are NOT organization-scoped;
they belong to the platform and join organizations via UserOrganization.

Design Rules:
- Email is globally unique (platform identity)
- hashed_password is nullable for SSO/OAuth users
- MFA fields support TOTP, SMS, and email-based second factors
- Soft delete via deleted_at (inherited from Base)
- version = optimistic locking (inherited from Base)
- CDC: sync to Databricks bronze.users_raw
"""
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Boolean, Integer, DateTime, Text, Index, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.membership import UserOrganization


class User(Base):
    """
    Platform identity. A user can belong to multiple organizations.

    Authentication: hashed_password (bcrypt) OR OAuth (hashed_password=NULL)
    MFA: TOTP | SMS | Email — enforced per security policy
    Lockout: tracked via failed_login_count + locked_until
    """
    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint(
            "mfa_method IN ('totp', 'sms', 'email') OR mfa_method IS NULL",
            name="ck_users_mfa_method",
        ),
        CheckConstraint(
            "failed_login_count >= 0",
            name="ck_users_failed_login_non_negative",
        ),
        # Partial index: only active, non-deleted users
        Index("idx_users_email_active", "email", postgresql_where="deleted_at IS NULL AND is_active = TRUE"),
        Index("idx_users_last_login_at", "last_login_at"),
        Index("idx_users_created_at", "created_at"),
    )

    # ── Identity ──────────────────────────────────────────────────────────────
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, nullable=False,
        comment="Primary identity — globally unique across platform",
    )
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Timestamp of email verification",
    )
    hashed_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="bcrypt hash; NULL for SSO/OAuth-only accounts",
    )

    # ── Profile ───────────────────────────────────────────────────────────────
    full_name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Display name"
    )
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    avatar_url: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Profile image CDN URL"
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="E.164 format"
    )
    phone_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Account Status ────────────────────────────────────────────────────────
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE",
        comment="FALSE = deactivated account",
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Platform superadmin — bypasses all org-level checks",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Email verified flag",
    )

    # ── Locale ────────────────────────────────────────────────────────────────
    locale: Mapped[str] = mapped_column(
        String(20), nullable=False, default="en-US", server_default="en-US"
    )
    timezone: Mapped[str] = mapped_column(
        String(100), nullable=False, default="UTC", server_default="UTC"
    )

    # ── Login Tracking ────────────────────────────────────────────────────────
    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_login_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IPv4 or IPv6"
    )
    login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    # ── MFA ───────────────────────────────────────────────────────────────────
    mfa_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    mfa_method: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, comment="totp | sms | email"
    )
    mfa_secret: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Encrypted TOTP secret (AES-256)"
    )

    # ── Security / Lockout ────────────────────────────────────────────────────
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Account locked until this timestamp (brute-force protection)",
    )
    password_changed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Onboarding ────────────────────────────────────────────────────────────
    onboarding_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE"
    )
    onboarding_step: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="Last completed onboarding step"
    )

    # ── Account Deletion Lifecycle ────────────────────────────────────────────
    deletion_requested_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When user requested account deletion",
    )
    scheduled_deletion_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Permanent deletion scheduled for this time (requested_at + 7 days)",
    )
    deletion_reason: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True, comment="Optional reason provided by user"
    )
    
    # ── Sprint 8.3.1 Phase 1: Authentication Hardening ─────────────────────
    is_locked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Whether the account is locked",
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Number of failed login attempts since last success",
    )
    change_password_required: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="FALSE",
        comment="Whether user must change their password on next login",
    )
    temporary_password: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Encrypted temporary password for first login",
    )
    temporary_password_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Expiry time for temporary password",
    )
    
    # ── Sprint 8.3.1 Phase 3: Account Lifecycle & Data Management ────────────
    deactivated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When user deactivated their own account (temporary suspension)",
    )
    deactivation_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True,
        comment="User-provided reason for self-deactivation",
    )
    last_export_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Last GDPR data export timestamp",
    )
    export_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0",
        comment="Number of times user has exported their data",
    )
    
    # ── Sprint 8.3.1 Phase 4: Security Hardening ────────────────────────
    mfa_recovery_codes_generated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="When MFA recovery codes were last generated",
    )
    trusted_devices_enabled: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="TRUE",
        comment="Whether user has device trust feature enabled",
    )
    trust_device_duration_days: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True, server_default="30",
        comment="How many days a trusted device remains trusted",
    )

    # ── Preferences ───────────────────────────────────────────────────────────
    preferences: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict,
        comment="UI preferences (theme, language, notification settings)",
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, default=dict,
        comment="Extensible metadata for internal tooling",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    memberships: Mapped[List["UserOrganization"]] = relationship(
        "UserOrganization", back_populates="user", cascade="all, delete-orphan", foreign_keys="[UserOrganization.user_id]"
    )
