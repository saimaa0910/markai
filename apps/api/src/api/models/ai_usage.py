import uuid
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database.base import Base


class AITokenUsage(Base):
    __tablename__ = "ai_token_usages"

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
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    cost_usd: Mapped[float] = mapped_column(Numeric(10, 6), default=0.000000, nullable=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)  # success | failure
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    retry_count: Mapped[Optional[int]] = mapped_column(Integer, default=0, nullable=True)
    capability: Mapped[Optional[str]] = mapped_column(String(50), default="text", nullable=True)
    agent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
