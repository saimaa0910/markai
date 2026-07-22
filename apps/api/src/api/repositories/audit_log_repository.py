"""
EAIMOS Audit Log Repository
===========================
Repository implementation for AuditLog model.
"""

from typing import Any, List
import uuid

from api.models.auth import AuditLog
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class AuditLogRepository(BaseRepository[AuditLog]):
    """Data access layer for System Audit Logs."""

    def __init__(self) -> None:
        super().__init__(AuditLog)

    async def list_by_organization(
        self,
        session: Any,
        organization_id: uuid.UUID,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """List audit events belonging to an organization."""
        filters = [FilterParam(field="organization_id", operator=FilterOperator.EQ, value=organization_id)]
        return await self.find_many(session=session, filters=filters, limit=limit, offset=offset)

    async def list_by_user(
        self,
        session: Any,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
    ) -> List[AuditLog]:
        """List audit events initiated by a specific user."""
        filters = [FilterParam(field="user_id", operator=FilterOperator.EQ, value=str(user_id))]
        return await self.find_many(session=session, filters=filters, limit=limit, offset=offset)
