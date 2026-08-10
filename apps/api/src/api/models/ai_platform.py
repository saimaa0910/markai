import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import ForeignKey, String, Boolean, Integer, Numeric, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class AIProvider(Base):
    __tablename__ = "ai_providers"

    name: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)  # groq, openai, anthropic, google, openrouter
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    base_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    api_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Provider default parameters
    default_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), default=0.70, nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=2048, nullable=True)
    streaming: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, nullable=True)

    # Relationships
    models: Mapped[List["AIModel"]] = relationship(
        "AIModel", back_populates="provider_rel", cascade="all, delete-orphan"
    )
    keys: Mapped[List["AIProviderKey"]] = relationship(
        "AIProviderKey", back_populates="provider_rel", cascade="all, delete-orphan"
    )
    health_checks: Mapped[List["AIProviderHealth"]] = relationship(
        "AIProviderHealth", back_populates="provider_rel", cascade="all, delete-orphan"
    )


class AIModel(Base):
    __tablename__ = "ai_models"
    __table_args__ = (
        Index("idx_ai_models_provider_id", "provider_id"),
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    context_window: Mapped[int] = mapped_column(Integer, nullable=False)
    
    input_token_price: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)  # price per 1M tokens
    output_token_price: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_tools: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_json: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_images: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    provider_rel: Mapped["AIProvider"] = relationship("AIProvider", back_populates="models")


class AIProviderKey(Base):
    __tablename__ = "ai_provider_keys"
    __table_args__ = (
        Index("idx_ai_provider_keys_provider_id", "provider_id"),
        Index("idx_ai_provider_keys_org_id", "organization_id"),
        Index("idx_ai_provider_keys_user_id", "user_id"),
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    api_key: Mapped[str] = mapped_column(String(255), nullable=False)  # Encrypted API Key
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
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

    # Relationships
    provider_rel: Mapped["AIProvider"] = relationship("AIProvider", back_populates="keys")


class AIProviderHealth(Base):
    __tablename__ = "ai_provider_health"
    __table_args__ = (
        Index("idx_ai_provider_health_provider_id", "provider_id"),
    )

    provider_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_providers.id", ondelete="CASCADE"),
        nullable=False,
    )
    latency: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_checked: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    provider_rel: Mapped["AIProvider"] = relationship("AIProvider", back_populates="health_checks")


class AIRequest(Base):
    __tablename__ = "ai_requests"

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
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.000000, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)


class AIUsage(Base):
    __tablename__ = "ai_usage"

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
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.000000, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AICost(Base):
    __tablename__ = "ai_costs"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.000000, nullable=False)


class AIPlaygroundSession(Base):
    __tablename__ = "ai_playground_sessions"

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
    name: Mapped[str] = mapped_column(String(100), default="New Session", nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float] = mapped_column(Numeric(4, 2), default=0.70, nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    messages: Mapped[List["AIPlaygroundMessage"]] = relationship(
        "AIPlaygroundMessage", back_populates="session_rel", cascade="all, delete-orphan"
    )


class AIPlaygroundMessage(Base):
    __tablename__ = "ai_playground_messages"

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_playground_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    session_rel: Mapped["AIPlaygroundSession"] = relationship("AIPlaygroundSession", back_populates="messages")


class AIOrgLimit(Base):
    __tablename__ = "ai_org_limits"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    credit_limit: Mapped[float] = mapped_column(Numeric(10, 2), default=100.00, nullable=False)
    credit_used: Mapped[float] = mapped_column(Numeric(10, 6), default=0.000000, nullable=False)
    rpm_limit: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    tpm_limit: Mapped[int] = mapped_column(Integer, default=50000, nullable=False)
