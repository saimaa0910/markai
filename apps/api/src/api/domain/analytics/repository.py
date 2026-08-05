"""
Analytics Repository.
"""

from typing import List, Any


class AnalyticsRepository:
    async def fetch_time_series(self) -> List[Any]:
        return []


analytics_repository = AnalyticsRepository()
