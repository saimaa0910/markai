"""
Integrations DTO.
"""

from dataclasses import dataclass


@dataclass
class IntegrationDTO:
    id: str
    provider: str
