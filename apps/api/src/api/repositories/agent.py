import uuid
from typing import Optional, List
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
