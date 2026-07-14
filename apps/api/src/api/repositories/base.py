from typing import Generic, TypeVar, Type, List, Optional, Tuple
import uuid
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from api.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    def __init__(self, model: Type[ModelType]) -> None:
        """
        Base repository with generic CRUD operations.
        Provides pagination, soft delete, and multi-tenant isolation.
        """
        self.model = model

    def get(self, db: Session, id: uuid.UUID) -> Optional[ModelType]:
        """Retrieve record by ID, excluding soft-deleted records."""
        return (
            db.query(self.model)
            .filter(self.model.id == id, self.model.deleted_at.is_(None))
            .first()
        )

    def list_by_org(
        self,
        db: Session,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ModelType]:
        """
        Paginated list of records under a specific organization tenant.
        Default page size is 50; max should be enforced at route level.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count_by_org(self, db: Session, organization_id: uuid.UUID) -> int:
        """Return total count of non-deleted records for an organization."""
        result = db.execute(
            select(func.count(self.model.id)).where(
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
        )
        return result.scalar_one()

    def list_paginated(
        self,
        db: Session,
        organization_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[ModelType], int]:
        """Return (items, total_count) tuple for pagination metadata."""
        items = self.list_by_org(db, organization_id, skip=skip, limit=limit)
        total = self.count_by_org(db, organization_id)
        return items, total

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: Optional[str] = None,
    ) -> ModelType:
        """Create a new record under organization with audit metadata."""
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
        """Update fields of an existing record with audit trail."""
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
        """Soft delete: sets deleted_at timestamp instead of removing the row."""
        db_obj.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        db_obj.updated_by = deleted_by
        db.commit()
        return db_obj
