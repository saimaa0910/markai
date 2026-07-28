import uuid
import datetime
from typing import Optional, List, Any
from sqlalchemy.orm import Session
from api.repositories.base import BaseRepository
from api.models.agent import AgentDefinition, AgentSession, AgentRun, AgentLog, AgentStatus


class AgentDefinitionRepository(BaseRepository[AgentDefinition]):
    def __init__(self) -> None:
        super().__init__(AgentDefinition)

    def get_by_id_and_org(
        self, db: Session, id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[AgentDefinition]:
        return (
            db.query(self.model)
            .filter(
                self.model.id == id,
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def list_active_by_org(
        self, db: Session, organization_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[AgentDefinition]:
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.status == AgentStatus.ACTIVE,
                self.model.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: str,
    ) -> AgentDefinition:
        data = dict(obj_in)
        data["organization_id"] = organization_id
        data["created_by"] = created_by
        data["updated_by"] = created_by
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def list_by_org(
        self, db: Session, organization_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[AgentDefinition]:
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None)
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_org(self, db: Session, organization_id: uuid.UUID) -> int:
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None)
            )
            .count()
        )

    def update(
        self, db: Session, db_obj: AgentDefinition, obj_in: dict, updated_by: str
    ) -> AgentDefinition:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db_obj.updated_by = updated_by
        if hasattr(db_obj, "version") and db_obj.version is not None:
            db_obj.version += 1
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db: Session, db_obj: AgentDefinition, deleted_by: str) -> None:
        db_obj.deleted_at = datetime.datetime.utcnow()
        db_obj.updated_by = deleted_by
        db.add(db_obj)
        db.commit()


class AgentSessionRepository(BaseRepository[AgentSession]):
    def __init__(self) -> None:
        super().__init__(AgentSession)

    def get_by_id_and_org(
        self, db: Session, id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[AgentSession]:
        return (
            db.query(self.model)
            .filter(
                self.model.id == id,
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def list_by_user_and_org(
        self, db: Session, user_id: uuid.UUID, organization_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[AgentSession]:
        return (
            db.query(self.model)
            .filter(
                self.model.user_id == user_id,
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: str,
    ) -> AgentSession:
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
        self, db: Session, db_obj: AgentSession, obj_in: dict, updated_by: str
    ) -> AgentSession:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        db_obj.updated_by = updated_by
        if hasattr(db_obj, "version") and db_obj.version is not None:
            db_obj.version += 1
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(self, db: Session, db_obj: AgentSession, deleted_by: str) -> None:
        db_obj.deleted_at = datetime.datetime.utcnow()
        db_obj.updated_by = deleted_by
        db.add(db_obj)
        db.commit()


class AgentRunRepository(BaseRepository[AgentRun]):
    def __init__(self) -> None:
        super().__init__(AgentRun)

    def list_by_session(
        self, db: Session, session_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> List[AgentRun]:
        return (
            db.query(self.model)
            .filter(
                self.model.session_id == session_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )


class AgentLogRepository(BaseRepository[AgentLog]):
    def __init__(self) -> None:
        super().__init__(AgentLog)

    def list_by_run(
        self, db: Session, run_id: uuid.UUID
    ) -> List[AgentLog]:
        return (
            db.query(self.model)
            .filter(
                self.model.run_id == run_id,
                self.model.deleted_at.is_(None),
            )
            .order_by(self.model.created_at.asc())
            .all()
        )


agent_definition_repo = AgentDefinitionRepository()
agent_session_repo = AgentSessionRepository()
agent_run_repo = AgentRunRepository()
agent_log_repo = AgentLogRepository()
