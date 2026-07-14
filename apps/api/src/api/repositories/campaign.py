import uuid
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


# Instantiate singletons for dependency sharing
campaign_repo = CampaignRepository()
campaign_template_repo = CampaignTemplateRepository()
campaign_analytics_repo = CampaignAnalyticsRepository()
