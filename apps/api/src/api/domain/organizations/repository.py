"""
Organizations Repository Database Access.
"""

from typing import Optional, Any


class OrganizationRepository:
    async def get_by_id(self, org_id: str) -> Optional[Any]:
        return None


org_repository = OrganizationRepository()
