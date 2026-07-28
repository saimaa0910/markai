import uuid
import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from api.repositories.base import BaseRepository
from api.models.campaign import Campaign, CampaignTemplate, CampaignAnalytics


class CampaignRepository(BaseRepository[Campaign]):
    def __init__(self) -> None:
        super().__init__(Campaign)

    def get_by_id_and_org(
        self, db: Session, id: uuid.UUID, organization_id: uuid.UUID
    ) -> Optional[Campaign]:
        """
        Fetch a single campaign verifying it belongs to the tenant organization.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.id == id,
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: Optional[str] = None,
    ) -> Campaign:
        data = dict(obj_in)
        data["organization_id"] = organization_id
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def list_by_org(self, db: Session, organization_id: uuid.UUID) -> List[Campaign]:
        return (
            db.query(self.model)
            .filter(
                self.model.organization_id == organization_id,
                self.model.deleted_at.is_(None)
            )
            .all()
        )

    def update(
        self,
        db: Session,
        db_obj: Campaign,
        obj_in: dict,
        updated_by: Optional[str] = None,
    ) -> Campaign:
        for field, value in obj_in.items():
            setattr(db_obj, field, value)
        if updated_by:
            db_obj.updated_by = updated_by
        if hasattr(db_obj, "version") and db_obj.version is not None:
            db_obj.version += 1
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def soft_delete(
        self,
        db: Session,
        db_obj: Campaign,
        deleted_by: Optional[str] = None,
    ) -> None:
        db_obj.deleted_at = datetime.datetime.utcnow()
        if deleted_by:
            db_obj.updated_by = deleted_by
        db.add(db_obj)
        db.commit()


class CampaignTemplateRepository(BaseRepository[CampaignTemplate]):
    def __init__(self) -> None:
        super().__init__(CampaignTemplate)

    def get_by_campaign_id(
        self, db: Session, campaign_id: uuid.UUID
    ) -> Optional[CampaignTemplate]:
        """
        Fetch template associated with campaign.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.campaign_id == campaign_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: Optional[str] = None,
    ) -> CampaignTemplate:
        data = dict(obj_in)
        data["organization_id"] = organization_id
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


class CampaignAnalyticsRepository(BaseRepository[CampaignAnalytics]):
    def __init__(self) -> None:
        super().__init__(CampaignAnalytics)

    def get_by_campaign_id(
        self, db: Session, campaign_id: uuid.UUID
    ) -> Optional[CampaignAnalytics]:
        """
        Fetch analytics associated with campaign.
        """
        return (
            db.query(self.model)
            .filter(
                self.model.campaign_id == campaign_id,
                self.model.deleted_at.is_(None),
            )
            .first()
        )

    def create(
        self,
        db: Session,
        obj_in: dict,
        organization_id: uuid.UUID,
        created_by: Optional[str] = None,
    ) -> CampaignAnalytics:
        data = dict(obj_in)
        data["organization_id"] = organization_id
        if created_by:
            data["created_by"] = created_by
            data["updated_by"] = created_by
        db_obj = self.model(**data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


campaign_repo = CampaignRepository()
campaign_template_repo = CampaignTemplateRepository()
campaign_analytics_repo = CampaignAnalyticsRepository()
