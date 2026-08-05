"""
CRM Repository Database Access.
"""

from typing import List, Any


class CRMRepository:
    async def get_all_contacts(self) -> List[Any]:
        return []


crm_repository = CRMRepository()
