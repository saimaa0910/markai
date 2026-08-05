"""
Auth Domain Events.
"""

from dataclasses import dataclass


@dataclass
class UserLoggedInEvent:
    user_id: str
    timestamp: float
