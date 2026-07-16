import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Boolean, Integer, Numeric, DateTime, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class AIRoutingPolicy(Base):
    __tablename__ = "ai_routing_policies"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    scope: Mapped[str] = mapped_column(String(50), default="global", nullable=False)  # global, organization, department, user, environment
    scope_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # store user ID or environment value
    
    request_type: Mapped[str] = mapped_column(String(50), default="*", nullable=False)
    routing_strategy: Mapped[str] = mapped_column(String(50), default="balanced", nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)  # JSON condition lists
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )


class AIRoutingLog(Base):
    __tablename__ = "ai_routing_logs"

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
    request_type: Mapped[str] = mapped_column(String(50), nullable=False)
    strategy_used: Mapped[str] = mapped_column(String(50), nullable=False)
    
    selected_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    selected_model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    fallback_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.000000, nullable=False)
    
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AIFailoverEvent(Base):
    __tablename__ = "ai_failover_events"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    failed_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    failed_model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    fallback_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    fallback_model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
