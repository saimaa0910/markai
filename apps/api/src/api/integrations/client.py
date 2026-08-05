"""
Third-Party API Integration Base Client.
"""

from typing import Dict, Any, Optional
import httpx


class IntegrationClient:
    """
    Base HTTP Client for external CRM, Analytics & Social Media integrations.
    """
    def __init__(self, base_url: str, api_key: Optional[str] = None) -> None:
        self.base_url = base_url
        self.api_key = api_key

    async def get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute GET request against third-party API.
        """
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
            response = await client.get(f"{self.base_url}{endpoint}", params=params, headers=headers)
            return response.json()
