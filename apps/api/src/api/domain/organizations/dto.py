"""
Organizations DTO.
"""

from dataclasses import dataclass


@dataclass
class OrganizationDTO:
    id: str
    name: str
    slug: str
