import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Index, Numeric, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.message import Message


class Conversation(Base):
    __tablename__ = "chat_conversations"

    title: Mapped[str] = mapped_column(String(255), nullable=False)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    is_archived: Mapped[bool] = mapped_column(default=False, server_default="0", nullable=False)
    is_favorite: Mapped[bool] = mapped_column(default=False, server_default="0", nullable=False)
    temperature: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    provider_name: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    __table_args__ = (
        Index("ix_chat_conversations_org_id", "organization_id"),
        Index("ix_chat_conversations_user_id", "user_id"),
        Index("ix_chat_conversations_created_at", "created_at"),
    )

    # Relationships
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
