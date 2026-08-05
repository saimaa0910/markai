"""
Analytics Pydantic Schemas.
"""

from pydantic import BaseModel


class AnalyticsOverviewSchema(BaseModel):
    total_impressions: int = 0
    total_clicks: int = 0
    ctr: float = 0.0
