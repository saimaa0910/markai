"""
EAIMOS Membership Repository
============================
Repository implementation for UserOrganization model.
Controls multi-tenant organization seat assignments and member roles.
"""

import datetime
from typing import Any, List, Optional
import uuid

from api.models.membership import UserOrganization, UserRole
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class UserOrganizationRepository(TenantRepository[UserOrganization]):
    """Data access layer for Organization Memberships."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(UserOrganization, organization_id=organization_id)

    async def create(
        self,
        session: Any,
        obj_in: dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> UserOrganization:
        data = dict(obj_in)
        if "joined_at" not in data:
            data["joined_at"] = datetime.datetime.now(datetime.timezone.utc)
        if "role" in data and isinstance(data["role"], str):
            # Normalize role string to enum if needed
            role_str = data["role"].upper()
            if role_str in UserRole.__members__:
                data["role"] = UserRole[role_str]
        return await super().create(session=session, obj_in=data, actor_id=actor_id)

    async def get_user_membership(
        self,
        session: Any,
        user_id: uuid.UUID,
    ) -> Optional[UserOrganization]:
        """Retrieve user's membership entry in the current organization."""
        filters = [FilterParam(field="user_id", operator=FilterOperator.EQ, value=user_id)]
        return await self.find_one(session=session, filters=filters)

    async def list_organization_members(
        self,
        session: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> List[UserOrganization]:
        """List active member assignments for the tenant organization."""
        return await self.find_many(session=session, limit=limit, offset=offset)
