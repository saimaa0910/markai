import uuid
from sqlalchemy import ForeignKey, String, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class ConversationShare(Base):
    __tablename__ = "chat_conversation_shares"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )
    shared_by_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    share_token: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    permission: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)  # "viewer", "editor"
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    conversation = relationship("Conversation", backref="shares")
    shared_by = relationship("User", backref="shares_created")
