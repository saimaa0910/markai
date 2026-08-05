"""
Analytics Controller.
"""

from typing import Dict, Any


class AnalyticsController:
    async def get_overview() -> Dict[str, Any]:
        return {"total_visitors": 0, "conversions": 0}


analytics_controller = AnalyticsController()
