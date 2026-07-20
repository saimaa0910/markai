import uuid
from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class ConversationBookmark(Base):
    __tablename__ = "chat_conversation_bookmarks"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    conversation = relationship("Conversation", backref="bookmarks")
    user = relationship("User", backref="chat_bookmarks")

    __table_args__ = (
        UniqueConstraint("user_id", "conversation_id", name="uq_chat_conversation_bookmark_user_conv"),
    )
