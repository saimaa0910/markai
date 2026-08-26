import uuid
from typing import Any, List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.models.integration import Integration, SyncJob, IntegrationProvider, IntegrationStatus
from api.schemas.integration import (
    IntegrationCreate,
    IntegrationUpdate,
    IntegrationResponse,
    SyncJobResponse,
)
from api.schemas.common import PaginatedResponse
from api.services.integration_service import IntegrationService, OAuthService
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

router = APIRouter(prefix="/integrations", tags=["integrations"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@router.post(
    "/",
    response_model=IntegrationResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_or_connect_integration(  # Sprint 8.3.1
    integration_in: IntegrationCreate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    # Standard connection endpoint
    return IntegrationService.connect_integration(
        db=db,
        organization_id=membership.organization_id,
        provider=integration_in.provider,
        name=integration_in.name,
        config=integration_in.config,
    )


@router.get("/", response_model=PaginatedResponse[IntegrationResponse])
def list_integrations(  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    skip = (page - 1) * page_size
    items = (
        db.query(Integration)
        .filter(
            Integration.organization_id == membership.organization_id,
            Integration.deleted_at.is_(None),
        )
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = (
        db.query(Integration)
        .filter(
            Integration.organization_id == membership.organization_id,
            Integration.deleted_at.is_(None),
        )
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.get("/oauth/url", response_model=Dict[str, str])
def get_oauth_authorization_url(  # Sprint 8.3.1
    provider: IntegrationProvider,
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    url = OAuthService.get_auth_url(provider.value, membership.organization_id)
    return {"url": url}


@router.post("/{integration_id}/sync", response_model=SyncJobResponse)
def trigger_integration_sync(  # Sprint 8.3.1
    integration_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    integration = (
        db.query(Integration)
        .filter(
            Integration.id == integration_id,
            Integration.organization_id == membership.organization_id,
            Integration.deleted_at.is_(None),
        )
        .first()
    )
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    # Perform synchronization sync/async
    job = IntegrationService.trigger_sync(
        db=db, integration=integration, triggered_by_user_id=membership.user_id
    )
    return job


@router.get("/{integration_id}/sync-jobs", response_model=PaginatedResponse[SyncJobResponse])
def list_sync_jobs(  # Sprint 8.3.1
    integration_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),  _auth: None = Depends(enforce_all_auth_policies),) -> Any:
    # Ensure access
    integration = (
        db.query(Integration)
        .filter(
            Integration.id == integration_id,
            Integration.organization_id == membership.organization_id,
            Integration.deleted_at.is_(None),
        )
        .first()
    )
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    skip = (page - 1) * page_size
    items = (
        db.query(SyncJob)
        .filter(SyncJob.integration_id == integration_id)
        .order_by(SyncJob.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = (
        db.query(SyncJob)
        .filter(SyncJob.integration_id == integration_id)
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.delete("/{integration_id}", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_integration(  # Sprint 8.3.1
    integration_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),  _auth: None = Depends(enforce_all_auth_policies),) -> None:
    integration = (
        db.query(Integration)
        .filter(
            Integration.id == integration_id,
            Integration.organization_id == membership.organization_id,
            Integration.deleted_at.is_(None),
        )
        .first()
    )
    if not integration:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Integration not found",
        )

    import datetime
    integration.deleted_at = datetime.datetime.now(datetime.timezone.utc)
    integration.status = IntegrationStatus.DISCONNECTED
    db.commit()
