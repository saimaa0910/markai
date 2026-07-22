"""
EAIMOS Organization Repository
===============================
Repository implementation for Organization model (Tenant Boundary).
"""

from typing import Any, List, Optional
import uuid
from sqlalchemy import select

from api.models.organization import Organization
from api.repositories.base import BaseRepository
from api.repositories.exceptions import EntityNotFoundError
from api.repositories.filters import FilterParam, FilterOperator
from api.repositories.query_builder import QueryOptions


class OrganizationRepository(BaseRepository[Organization]):
    """Data access layer for tenant Organizations."""

    def __init__(self) -> None:
        super().__init__(Organization)

    async def get_by_slug(
        self,
        session: Any,
        slug: str,
        include_deleted: bool = False,
    ) -> Optional[Organization]:
        """Lookup organization by unique URL slug."""
        filters = [FilterParam(field="slug", operator=FilterOperator.EQ, value=slug)]
        return await self.find_one(session=session, filters=filters, include_deleted=include_deleted)

    async def get_active_organizations(
        self,
        session: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Organization]:
        """Retrieve list of active, non-suspended tenant organizations."""
        filters = [FilterParam(field="is_active", operator=FilterOperator.EQ, value=True)]
        return await self.find_many(session=session, filters=filters, limit=limit, offset=offset)

    async def update_tier(
        self,
        session: Any,
        org_id: uuid.UUID,
        new_tier: str,
        max_members: Optional[int] = None,
        max_ai_credits: Optional[float] = None,
        actor_id: Optional[str] = None,
    ) -> Organization:
        """Update organization plan tier and limits."""
        payload: dict[str, Any] = {"plan_tier": new_tier}
        if max_members is not None:
            payload["max_members"] = max_members
        if max_ai_credits is not None:
            payload["max_ai_credits"] = max_ai_credits

        return await self.update(session, org_id, payload, actor_id=actor_id)
