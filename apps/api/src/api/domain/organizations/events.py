"""
Organizations Events.
"""

from dataclasses import dataclass


@dataclass
class OrganizationCreatedEvent:
    org_id: str
    name: str
