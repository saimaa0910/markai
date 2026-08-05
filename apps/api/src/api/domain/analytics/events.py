"""
Analytics Events.
"""

from dataclasses import dataclass


@dataclass
class MetricRecordedEvent:
    metric_name: str
    value: float
