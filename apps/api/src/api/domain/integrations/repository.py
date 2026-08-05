"""
Integrations Repository.
"""

from typing import Optional, Any


class IntegrationRepository:
    async def get_by_provider(self, provider: str) -> Optional[Any]:
        return None


integration_repository = IntegrationRepository()
