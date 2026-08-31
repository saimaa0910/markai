import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import ForeignKey, String, Boolean, Integer, Numeric, DateTime, Text, JSON, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class AISecurityPolicyRule(Base):
    __tablename__ = "ai_security_policy_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), default="global", nullable=False)  # global, organization, user
    request_type: Mapped[str] = mapped_column(String(50), default="*", nullable=False)  # chat, embeddings, vision, json, *
    
    # JSON arrays of strings: ["openai", "google"]
    allowed_providers: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    allowed_models: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    
    # Limits & Quotas
    daily_token_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_request_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_token_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_request_limit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    daily_budget_usd: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    monthly_budget_usd: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    
    # Category Actions JSON dict: {"violence": "block", "pii": "redact", "secrets": "block"}
    moderation_actions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    pii_masking_policy: Mapped[str] = mapped_column(String(50), default="redact", nullable=False)  # redact, mask, replace
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )


class AISecurityEvent(Base):
    __tablename__ = "ai_security_events"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)  # policy_violation, prompt_injection, pii_leak, secret_leak, budget_exceeded
    severity: Mapped[str] = mapped_column(String(20), default="medium", nullable=False)  # low, medium, high, critical
    trigger_source: Mapped[str] = mapped_column(String(20), nullable=False)  # input, output
    
    details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    action_taken: Mapped[str] = mapped_column(String(20), default="block", nullable=False)  # block, redact, warn, allow


class AIScanLog(Base):
    __tablename__ = "ai_scan_logs"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    prompt_length: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    prompt_complexity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric(4, 2), default=0.00, nullable=False)
    
    pii_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    secrets_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    injection_risk: Mapped[float] = mapped_column(Numeric(4, 2), default=0.00, nullable=False)
    classification: Mapped[str] = mapped_column(String(50), default="safe", nullable=False)


class AIQuotaUsage(Base):
    __tablename__ = "ai_quota_usages"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    daily_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_requests: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    daily_spend: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    monthly_spend: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    
    last_reset_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )


# =============================================================================
# Sprint 8.3.1 Phase 4: Authentication Security Models
# =============================================================================


class TrustedDevice(Base):
    """Trusted Device - Sprint 8.3.1 Phase 4
    
    Stores devices that have been marked as trusted by users, allowing MFA bypass
    for a configured duration.
    """
    __tablename__ = "trusted_devices"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Optimistic locking counter",
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    device_fingerprint: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Unique device identifier"
    )
    device_name: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="User-friendly device name"
    )
    device_type: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, comment="mobile, desktop, tablet"
    )
    browser: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Browser name and version"
    )
    os: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True, comment="Operating system"
    )
    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP address when trusted"
    )
    location: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Geo-location when trusted"
    )
    trusted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="When device was trusted"
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When trust expires (NULL = never)"
    )
    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Last time this device was used"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, comment="Whether trust is still active"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When trust was revoked"
    )
    revoked_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who revoked (for admin revocations)",
    )
    revoke_reason: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Reason for revocation"
    )


class MFARecoveryCode(Base):
    """MFA Recovery Code - Sprint 8.3.1 Phase 4
    
    Backup authentication codes for MFA recovery.
    Codes are stored as SHA-256 hashes and are single-use.
    """
    __tablename__ = "mfa_recovery_codes"
    
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Optimistic locking counter",
    )
    
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    code_hash: Mapped[str] = mapped_column(
        Text, nullable=False, comment="SHA-256 hash of recovery code"
    )
    is_used: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Whether code has been used"
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="When code was used"
    )
    used_from_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IP address where code was used"
    )


import uuid as _uuid

class RateLimitLog(Base):
    """Rate Limit Log - Sprint 8.3.1 Phase 4

    Tracks rate limit attempts and blocks for security monitoring and forensics.
    """
    __tablename__ = "rate_limit_log"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        default=uuid.uuid4,
    )
    
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default="1",
        comment="Optimistic locking counter",
    )
    
    endpoint: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="API endpoint that was rate limited"
    )
    ip_address: Mapped[str] = mapped_column(
        String(45), nullable=False, comment="IP address of request"
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User ID if authenticated",
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, comment="Number of attempts in this window"
    )
    window_start: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Start of rate limit window"
    )
    window_end: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="End of rate limit window"
    )
    blocked: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="Whether request was blocked"
    )
