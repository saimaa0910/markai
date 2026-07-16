import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy import ForeignKey, String, Boolean, Integer, Numeric, DateTime, Text, JSON
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
