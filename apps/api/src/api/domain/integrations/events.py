"""
Integrations Events.
"""

from dataclasses import dataclass


@dataclass
class IntegrationConnectedEvent:
    provider: str
    status: str
