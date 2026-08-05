"""
Campaigns Domain Service — Business Logic Delegation.
Delegates to existing CampaignService implementation.
"""

import uuid
from typing import List, Any
from sqlalchemy.orm import Session
from api.services.campaign_service import CampaignService as BaseCampaignService
from api.schemas.campaign import CampaignCreate, CampaignUpdate


class CampaignDomainService:
    def create_campaign(self, db: Session, campaign_in: CampaignCreate, organization_id: uuid.UUID, created_by: str) -> Any:
        return BaseCampaignService.create_campaign(db, campaign_in=campaign_in, organization_id=organization_id, created_by=created_by)

    def list_campaigns(self, db: Session, organization_id: uuid.UUID) -> List[Any]:
        return BaseCampaignService.list_campaigns(db, organization_id=organization_id)

    def get_campaign(self, db: Session, campaign_id: uuid.UUID, organization_id: uuid.UUID) -> Any:
        return BaseCampaignService.get_campaign(db, campaign_id=campaign_id, organization_id=organization_id)

    def update_campaign(self, db: Session, campaign_id: uuid.UUID, campaign_in: CampaignUpdate, organization_id: uuid.UUID, updated_by: str) -> Any:
        return BaseCampaignService.update_campaign(db, campaign_id=campaign_id, campaign_in=campaign_in, organization_id=organization_id, updated_by=updated_by)

    def delete_campaign(self, db: Session, campaign_id: uuid.UUID, organization_id: uuid.UUID, deleted_by: str) -> None:
        BaseCampaignService.delete_campaign(db, campaign_id=campaign_id, organization_id=organization_id, deleted_by=deleted_by)


campaign_domain_service = CampaignDomainService()
