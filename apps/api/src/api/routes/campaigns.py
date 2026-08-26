import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.services.campaign_service import CampaignService
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1
from api.schemas.campaign import (
    CampaignCreate,
    CampaignUpdate,
    CampaignResponse,
    CampaignTrackRequest,
)

campaigns_router = APIRouter(prefix="/campaigns", tags=["campaigns"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@campaigns_router.post(
    "/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED
)
def create_campaign(
    campaign_in: CampaignCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Create a new marketing campaign, campaign template, and metrics tracker.
    """
    return CampaignService.create_campaign(
        db,
        campaign_in=campaign_in,
        organization_id=membership.organization_id,
        created_by=str(current_user.id),
    )


@campaigns_router.get("/", response_model=List[CampaignResponse])
def list_campaigns(
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    List all active campaigns for the current tenant organization.
    """
    return CampaignService.list_campaigns(db, organization_id=membership.organization_id)


@campaigns_router.get("/{campaign_id}", response_model=CampaignResponse)
def get_campaign(
    campaign_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    Retrieve details, template, and analytics for a campaign.
    """
    return CampaignService.get_campaign(
        db, campaign_id=campaign_id, organization_id=membership.organization_id
    )


@campaigns_router.put("/{campaign_id}", response_model=CampaignResponse)
def update_campaign(
    campaign_id: uuid.UUID,
    campaign_in: CampaignUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> Any:
    """
    Modify attributes of an existing campaign, including its lifecycle state.
    """
    return CampaignService.update_campaign(
        db,
        campaign_id=campaign_id,
        campaign_in=campaign_in,
        organization_id=membership.organization_id,
        updated_by=str(current_user.id),
    )


@campaigns_router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_campaign(
    campaign_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Soft-delete a campaign from the database.
    """
    CampaignService.delete_campaign(
        db,
        campaign_id=campaign_id,
        organization_id=membership.organization_id,
        deleted_by=str(current_user.id),
    )


@campaigns_router.post("/{campaign_id}/execute", response_model=CampaignResponse)
def execute_campaign(
    campaign_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    Trigger campaign run execution and populate simulated performance delivery logs.
    """
    return CampaignService.execute_campaign(
        db, campaign_id=campaign_id, organization_id=membership.organization_id
    )


@campaigns_router.post("/{campaign_id}/track", response_model=CampaignResponse)
def track_event(
    campaign_id: uuid.UUID,
    track_in: CampaignTrackRequest,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    Record clicks/conversions/impressions for A/B creative variants.
    """
    return CampaignService.track_event(
        db,
        campaign_id=campaign_id,
        track_in=track_in,
        organization_id=membership.organization_id,
    )
