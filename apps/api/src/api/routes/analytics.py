import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database.session import get_db
from api.core.deps import RoleChecker
from api.models.membership import UserOrganization, UserRole
from api.services.analytics_service import AnalyticsService
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

router = APIRouter(prefix="/analytics", tags=["analytics"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@router.get("/executive")
def get_executive_report(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    """
    Returns an aggregated corporate dashboard report including AI cost audit,
    campaign performance metrics, and CRM pipeline values.
    """
    return AnalyticsService.get_executive_summary(
        db=db, organization_id=membership.organization_id
    )


@router.get("/token-usage")
def get_token_usage_report(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    days: int = Query(7, ge=1, le=90),
) -> Any:
    """
    Returns day-by-day aggregate trends of AI Token execution cost
    and count metrics for visual chart rendering.
    """
    return AnalyticsService.get_token_usage_trends(
        db=db, organization_id=membership.organization_id, days=days
    )
