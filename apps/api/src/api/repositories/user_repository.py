"""
EAIMOS User Repository
======================
Repository implementation for User model.
"""

from typing import Any, List, Optional
import uuid
from api.models.user import User
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class UserRepository(BaseRepository[User]):
    """Data access layer for Platform Users."""

    def __init__(self) -> None:
        super().__init__(User)

    async def get_by_email(
        self,
        session: Any,
        email: str,
        include_deleted: bool = False,
    ) -> Optional[User]:
        """Lookup user by email address."""
        filters = [FilterParam(field="email", operator=FilterOperator.EQ, value=email.lower().strip())]
        return await self.find_one(session=session, filters=filters, include_deleted=include_deleted)

    async def get_active_users(
        self,
        session: Any,
        limit: int = 50,
        offset: int = 0,
    ) -> List[User]:
        """List all active platform users."""
        filters = [FilterParam(field="is_active", operator=FilterOperator.EQ, value=True)]
        return await self.find_many(session=session, filters=filters, limit=limit, offset=offset)
