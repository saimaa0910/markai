import uuid
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import or_
from api.repositories.base import BaseRepository
from api.models.conversation import Conversation
from api.models.message import Message


class ConversationRepository(BaseRepository[Conversation]):
    def __init__(self) -> None:
        super().__init__(Conversation)

    def get_by_id_and_org(
        self, db: Session, id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[Conversation]:
        """Fetch a single conversation verifying it belongs to the tenant organization."""
        return (
            db.query(self.model)
            .filter(
                self.model.id == id,
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_org_and_user(
        self, db: Session, organization_id: uuid.UUID, user_id: uuid.UUID
    ) -> List[Conversation]:
        """Fetch all active conversations under org and user, excluding archived unless explicitly filtered."""
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.user_id == user_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.desc())
            .all()
        )

    def search_conversations(
        self, db: Session, organization_id: uuid.UUID, user_id: uuid.UUID, query: str
    ) -> List[Conversation]:
        """Search conversations in title case-insensitively."""
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.user_id == user_id,
                self.model.title.ilike(f"%{query}%"),
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.desc())
            .all()
        )


class MessageRepository(BaseRepository[Message]):
    def __init__(self) -> None:
        super().__init__(Message)

    def get_by_conversation_id(
        self, db: Session, conversation_id: uuid.UUID
    ) -> List[Message]:
        """Get all messages belonging to a conversation ordered chronologically."""
        return (
            db.query(self.model)
            .filter(
                self.model.conversation_id == conversation_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.asc())
            .all()
        )


# Instantiate repository singletons
conversation_repo = ConversationRepository()
message_repo = MessageRepository()
