"""
CRM Events.
"""

from dataclasses import dataclass


@dataclass
class ContactCreatedEvent:
    contact_id: str
    email: str
