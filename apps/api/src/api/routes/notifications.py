import uuid
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.database.session import get_db
from api.core.deps import RoleChecker, get_current_user
from api.models.membership import UserOrganization, UserRole
from api.models.user import User
from api.models.integration import Notification, NotificationPreference, NotificationChannel
from api.schemas.notification import (
    NotificationResponse,
    NotificationPreferenceResponse,
    NotificationPreferenceUpdate,
)
from api.schemas.common import PaginatedResponse
from api.services.notification_service import NotificationService
from api.middleware.auth_enforcement import enforce_all_auth_policies  # Sprint 8.3.1

router = APIRouter(prefix="/notifications", tags=["notifications"])
active_member = RoleChecker([UserRole.OWNER, UserRole.ADMIN, UserRole.MEMBER])


@router.get("/", response_model=PaginatedResponse[NotificationResponse])
def list_notifications(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
    is_read: Optional[bool] = Query(None),
    channel: Optional[NotificationChannel] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> Any:
    skip = (page - 1) * page_size
    filters = [
        Notification.user_id == membership.user_id,
        Notification.organization_id == membership.organization_id,
        Notification.deleted_at.is_(None),
    ]
    if is_read is not None:
        filters.append(Notification.is_read == is_read)
    if channel is not None:
        filters.append(Notification.channel == channel)

    items = (
        db.query(Notification)
        .filter(and_(*filters))
        .order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(page_size)
        .all()
    )
    total = (
        db.query(Notification)
        .filter(and_(*filters))
        .count()
    )
    return PaginatedResponse.build(
        items=items, total=total, page=page, page_size=page_size
    )


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_as_read(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == membership.user_id,
            Notification.deleted_at.is_(None),
        )
        .first()
    )
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification not found",
        )

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@router.post("/read-all", status_code=status.HTTP_200_OK)
def mark_all_notifications_as_read(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == membership.user_id,
            Notification.organization_id == membership.organization_id,
            Notification.is_read == False,
            Notification.deleted_at.is_(None),
        )
        .all()
    )
    for n in notifications:
        n.is_read = True
    db.commit()
    return {"success": True, "marked_count": len(notifications)}


@router.get("/preferences", response_model=List[NotificationPreferenceResponse])
def get_notification_preferences(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    return NotificationService.get_user_preferences(
        db=db, user_id=membership.user_id, organization_id=membership.organization_id
    )


@router.patch("/preferences/{pref_id}", response_model=NotificationPreferenceResponse)
def update_notification_preference(
    _: None = Depends(enforce_all_auth_policies),  # Sprint 8.3.1
    pref_id: uuid.UUID,
    pref_in: NotificationPreferenceUpdate,
    db: Session = Depends(get_db),
    membership: UserOrganization = Depends(active_member),
) -> Any:
    pref = (
        db.query(NotificationPreference)
        .filter(
            NotificationPreference.id == pref_id,
            NotificationPreference.user_id == membership.user_id,
            NotificationPreference.deleted_at.is_(None),
        )
        .first()
    )
    if not pref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Notification preference not found",
        )

    update_data = pref_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(pref, field, value)

    db.commit()
    db.refresh(pref)
    return pref
