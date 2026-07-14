import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String, Boolean, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class AIModelRegistry(Base):
    __tablename__ = "ai_models_registry"

    provider: Mapped[str] = mapped_column(String(50), nullable=False)  # groq, openrouter, openai, anthropic, gemini
    model_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    context_window: Mapped[int] = mapped_column(Integer, nullable=False)
    
    supports_streaming: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    supports_vision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_json: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_images: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_audio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_tool_calling: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_embeddings: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    input_token_price: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)  # price per 1M tokens
    output_token_price: Mapped[float] = mapped_column(Numeric(10, 4), default=0.0000, nullable=False)
    
    latency: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)  # avg latency in seconds
    priority: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_healthy: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Every table must include organization_id. Nullable support for system-wide models.
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Relationships
    routing_rules: Mapped[list["AIRoutingRule"]] = relationship(
        "AIRoutingRule", back_populates="model", cascade="all, delete-orphan"
    )


class AIRoutingRule(Base):
    __tablename__ = "ai_routing_rules"

    request_type: Mapped[str] = mapped_column(String(50), nullable=False)  # chat, content, vision, embeddings, json
    
    model_registry_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_models_registry.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Tenant override capability
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )

    # Relationships
    model: Mapped["AIModelRegistry"] = relationship(
        "AIModelRegistry", back_populates="routing_rules"
    )
