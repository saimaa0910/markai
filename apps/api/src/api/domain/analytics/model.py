"""
Analytics Model Entity.
"""

from pydantic import BaseModel


class MetricPointEntity(BaseModel):
    timestamp: str
    metric_name: str
    value: float
