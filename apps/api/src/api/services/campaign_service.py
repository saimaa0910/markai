import uuid
from decimal import Decimal
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from api.models.campaign import Campaign, CampaignStatus, CampaignChannel
from api.repositories.campaign import (
    campaign_repo,
    campaign_template_repo,
    campaign_analytics_repo,
)
from api.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignTrackRequest


class CampaignService:
    @staticmethod
    def create_campaign(
        db: Session,
        campaign_in: CampaignCreate,
        organization_id: uuid.UUID,
        created_by: Optional[str] = None,
    ) -> Campaign:
        """
        Business Rule: Create campaign, its email/social templates, and initial analytics record.
        """
        # 1. Map campaign fields
        campaign_data = {
            "title": campaign_in.title,
            "description": campaign_in.description,
            "budget": campaign_in.budget,
            "channel": campaign_in.channel,
            "scheduled_for": campaign_in.scheduled_for,
            "status": (
                CampaignStatus.SCHEDULED
                if campaign_in.scheduled_for
                else CampaignStatus.DRAFT
            ),
        }

        campaign = campaign_repo.create(
            db,
            obj_in=campaign_data,
            organization_id=organization_id,
            created_by=created_by,
        )

        # 2. Create the associated template
        template_data = {
            "campaign_id": campaign.id,
            "title": campaign_in.template.title,
            "subject": campaign_in.template.subject,
            "content_a": campaign_in.template.content_a,
            "content_b": campaign_in.template.content_b,
        }
        campaign_template_repo.create(
            db,
            obj_in=template_data,
            organization_id=organization_id,
            created_by=created_by,
        )

        # 3. Initialize blank performance metrics tracker
        analytics_data = {
            "campaign_id": campaign.id,
            "impressions_a": 0,
            "clicks_a": 0,
            "conversions_a": 0,
            "impressions_b": 0,
            "clicks_b": 0,
            "conversions_b": 0,
            "revenue": 0.00,
        }
        campaign_analytics_repo.create(
            db,
            obj_in=analytics_data,
            organization_id=organization_id,
            created_by=created_by,
        )

        db.refresh(campaign)
        return campaign

    @staticmethod
    def get_campaign(
        db: Session, campaign_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Campaign:
        """
        Business Rule: Retrieve campaign details, verifying multi-tenant isolation.
        """
        campaign = campaign_repo.get_by_id_and_org(db, campaign_id, organization_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found or access denied",
            )
        return campaign

    @staticmethod
    def list_campaigns(db: Session, organization_id: uuid.UUID) -> List[Campaign]:
        """
        Business Rule: List all active campaigns for the current organization.
        """
        return campaign_repo.list_by_org(db, organization_id)

    @staticmethod
    def update_campaign(
        db: Session,
        campaign_id: uuid.UUID,
        campaign_in: CampaignUpdate,
        organization_id: uuid.UUID,
        updated_by: Optional[str] = None,
    ) -> Campaign:
        """
        Business Rule: Validate state transition sequence and update fields.
        """
        campaign = CampaignService.get_campaign(db, campaign_id, organization_id)

        # Validate status change sequence if provided
        if campaign_in.status and campaign_in.status != campaign.status:
            current = campaign.status
            target = campaign_in.status

            allowed = False
            # Draft can go to Scheduled, Active, or Archived
            if current == CampaignStatus.DRAFT:
                allowed = target in [
                    CampaignStatus.SCHEDULED,
                    CampaignStatus.ACTIVE,
                    CampaignStatus.ARCHIVED,
                ]
            # Scheduled can go to Active or Archived
            elif current == CampaignStatus.SCHEDULED:
                allowed = target in [CampaignStatus.ACTIVE, CampaignStatus.ARCHIVED]
            # Active can go to Completed or Archived
            elif current == CampaignStatus.ACTIVE:
                allowed = target in [CampaignStatus.COMPLETED, CampaignStatus.ARCHIVED]
            # Completed can go to Archived
            elif current == CampaignStatus.COMPLETED:
                allowed = target == CampaignStatus.ARCHIVED
            # Archived status is terminal
            elif current == CampaignStatus.ARCHIVED:
                allowed = False

            if not allowed:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid state transition from {current} to {target}",
                )

        # Filter out none values for update schema
        update_data = campaign_in.model_dump(exclude_unset=True)
        return campaign_repo.update(db, campaign, update_data, updated_by=updated_by)

    @staticmethod
    def delete_campaign(
        db: Session,
        campaign_id: uuid.UUID,
        organization_id: uuid.UUID,
        deleted_by: Optional[str] = None,
    ) -> None:
        """
        Business Rule: Soft-delete a campaign.
        """
        campaign = CampaignService.get_campaign(db, campaign_id, organization_id)
        campaign_repo.soft_delete(db, campaign, deleted_by=deleted_by)

    @staticmethod
    def execute_campaign(
        db: Session, campaign_id: uuid.UUID, organization_id: uuid.UUID
    ) -> Campaign:
        """
        Business Rule: Launch a campaign, transition status to ACTIVE, and generate
        initial simulated marketing analytics to mock delivery execution metrics.
        """
        campaign = CampaignService.get_campaign(db, campaign_id, organization_id)

        if campaign.status == CampaignStatus.ARCHIVED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Archived campaigns cannot be executed.",
            )

        # Transition status to ACTIVE
        campaign.status = CampaignStatus.ACTIVE
        db.commit()

        # Simulate A/B performance metrics (to represent execution delivery logs)
        analytics = campaign.analytics
        if analytics:
            # Variant A: Higher impressions, moderate clicks, standard conversions
            analytics.impressions_a += 1200
            analytics.clicks_a += 120
            analytics.conversions_a += 12
            # Variant B: Lower impressions, higher clicks, higher conversions
            analytics.impressions_b += 1000
            analytics.clicks_b += 150
            analytics.conversions_b += 20
            # Calculate mock revenue
            analytics.revenue += Decimal("850.00")
            db.commit()

        db.refresh(campaign)
        return campaign

    @staticmethod
    def track_event(
        db: Session,
        campaign_id: uuid.UUID,
        track_in: CampaignTrackRequest,
        organization_id: uuid.UUID,
    ) -> Campaign:
        """
        Business Rule: Track an impression, click, or conversion event for A/B variant.
        """
        campaign = CampaignService.get_campaign(db, campaign_id, organization_id)

        if campaign.status != CampaignStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Events can only be tracked for active campaigns.",
            )

        analytics = campaign.analytics
        if not analytics:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Analytics tracker not initialized.",
            )

        variant = track_in.variant.upper()
        event = track_in.event_type.lower()

        if variant == "A":
            if event == "impression":
                analytics.impressions_a += 1
            elif event == "click":
                analytics.clicks_a += 1
            elif event == "conversion":
                analytics.conversions_a += 1
                analytics.revenue += Decimal(str(track_in.revenue_generated))
        elif variant == "B":
            if event == "impression":
                analytics.impressions_b += 1
            elif event == "click":
                analytics.clicks_b += 1
            elif event == "conversion":
                analytics.conversions_b += 1
                analytics.revenue += Decimal(str(track_in.revenue_generated))

        db.commit()
        db.refresh(campaign)
        return campaign
