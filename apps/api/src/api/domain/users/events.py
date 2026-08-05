"""
Users Domain Events.
"""

from dataclasses import dataclass


@dataclass
class UserCreatedEvent:
    user_id: str
    email: str
