import uuid
from typing import Optional, List, Any
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

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: str,
    ) -> Conversation:
        data = dict(obj_in)
        data["organization_id"] = organization_id
        data["created_by"] = created_by
        data["updated_by"] = created_by
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, db_obj: Any, obj_in: dict, updated_by: str
    ) -> Conversation:
        if not isinstance(db_obj, self.model):
            db_obj = db.query(self.model).filter(self.model.id == db_obj).first()
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db_obj.updated_by = updated_by
        if hasattr(db_obj, "version") and db_obj.version is not None:
            db_obj.version += 1
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db: Session, db_obj: Any, deleted_by: str) -> None:
        import datetime
        if not isinstance(db_obj, self.model):
            db_obj = db.query(self.model).filter(self.model.id == db_obj).first()
        db_obj.deleted_at = datetime.datetime.utcnow()
        db_obj.updated_by = deleted_by
        db.add(db_obj)
        db.commit()


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

    def create(
        self,
        db: Session,
        obj_in: dict,
        created_by: str,
    ) -> Message:
        data = dict(obj_in)
        data["created_by"] = created_by
        data["updated_by"] = created_by
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, db_obj: Any, obj_in: dict, updated_by: str
    ) -> Message:
        if not isinstance(db_obj, self.model):
            db_obj = db.query(self.model).filter(self.model.id == db_obj).first()
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db_obj.updated_by = updated_by
        if hasattr(db_obj, "version") and db_obj.version is not None:
            db_obj.version += 1
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db: Session, db_obj: Any, deleted_by: str) -> None:
        import datetime
        if not isinstance(db_obj, self.model):
            db_obj = db.query(self.model).filter(self.model.id == db_obj).first()
        db_obj.deleted_at = datetime.datetime.utcnow()
        db_obj.updated_by = deleted_by
        db.add(db_obj)
        db.commit()


# Instantiate repository singletons
conversation_repo = ConversationRepository()
message_repo = MessageRepository()
