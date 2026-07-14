from typing import Generic, TypeVar, Type, List, Optional
import uuid
import datetime
from sqlalchemy.orm import Session
from api.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]) -> None:
        """
        Base repository with generic operations for Clean Architecture.
        """
        self.model = model

    def get(self, db: Session, id: uuid.UUID) -> Optional[ModelType]:
        """
        Retrieve record by ID, ensuring it has not been soft-deleted.
        """
        return (
            db.query(self.model)
            .filter(self.model.id == id, self.model.deleted_at.is_(None))
            .first()
        )

    def list_by_org(self, db: Session, organization_id: uuid.UUID) -> List[ModelType]:
        """
        Retrieve list of records under specific organization tenant.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .all()
        )

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: Optional[str] = None,
    ) -> ModelType:
        """
        Create a new database record under organization.
        """
        db_obj = self.model(
            **obj_in,
            organization_id=organization_id,
            created_by=created_by,
            updated_by=created_by,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        db_obj: ModelType,
        obj_in: dict,
        updated_by: Optional[str] = None,
    ) -> ModelType:
        """
        Update fields of an existing record.
        """
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db_obj.updated_by = updated_by
        db_obj.updated_at = datetime.datetime.now(datetime.timezone.utc)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(
        self, db: Session, db_obj: ModelType, deleted_by: Optional[str] = None
    ) -> ModelType:
        """
        Perform soft delete by marking deleted_at.
        """
        db_obj.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        db_obj.updated_by = deleted_by
        db.commit()
        return db_obj
