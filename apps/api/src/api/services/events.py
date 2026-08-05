"""
Service Layer Base Events.
"""

from dataclasses import dataclass


@dataclass
class ServiceExecutedEvent:
    service_name: str
    status: str
