"""
CRM DTO.
"""

from dataclasses import dataclass


@dataclass
class ContactDTO:
    id: str
    email: str
    name: str
