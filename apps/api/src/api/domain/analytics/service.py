"""
Analytics Service.
"""

from typing import Dict, Any


class AnalyticsService:
    async def aggregate_metrics(self) -> Dict[str, Any]:
        return {}


analytics_service = AnalyticsService()
