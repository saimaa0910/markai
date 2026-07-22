"""
EAIMOS Notifications Repository Module — Sprint 11
==================================================
Repository implementations for Notifications models:
Notification, NotificationPreference, NotificationTemplate.
"""

from typing import Any, List, Optional
import uuid

from api.models.integration import Notification, NotificationPreference
from api.models.notification_templates import NotificationTemplate
from api.repositories.tenant import TenantRepository
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class NotificationRepository(TenantRepository[Notification]):
    """Data access layer for In-App and Push Notifications."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Notification, organization_id=organization_id)

    async def list_unread_for_user(self, session: Any, user_id: uuid.UUID) -> List[Notification]:
        filters = [
            FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_id),
            FilterParam(field="is_read", operator=FilterOperator.EQ, value=False),
        ]
        return await self.find_many(session=session, filters=filters)


class NotificationPreferenceRepository(BaseRepository[NotificationPreference]):
    """Data access layer for User Notification Preferences."""

    def __init__(self) -> None:
        super().__init__(NotificationPreference)

    async def get_by_user(self, session: Any, user_id: uuid.UUID) -> Optional[NotificationPreference]:
        filters = [FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_id)]
        return await self.find_one(session=session, filters=filters)


class NotificationTemplateRepository(TenantRepository[NotificationTemplate]):
    """Data access layer for Custom Notification Templates."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(NotificationTemplate, organization_id=organization_id)
