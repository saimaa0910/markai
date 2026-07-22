"""
EAIMOS System Config Repository
===============================
Repository implementation for SystemConfiguration model.
"""

from typing import Any, Optional
from api.models.admin import SystemConfiguration
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class SystemConfigRepository(BaseRepository[SystemConfiguration]):
    """Data access layer for global System Configurations."""

    def __init__(self) -> None:
        super().__init__(SystemConfiguration)

    async def get_by_key(
        self,
        session: Any,
        key: str,
        namespace: str = "default",
    ) -> Optional[SystemConfiguration]:
        """Retrieve system config entry by configuration key and namespace."""
        filters = [
            FilterParam(field="key", operator=FilterOperator.EQ, value=key),
            FilterParam(field="namespace", operator=FilterOperator.EQ, value=namespace),
        ]
        return await self.find_one(session=session, filters=filters)
