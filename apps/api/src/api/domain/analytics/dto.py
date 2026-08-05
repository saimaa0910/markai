"""
Analytics DTO.
"""

from dataclasses import dataclass


@dataclass
class MetricDTO:
    name: str
    val: float
