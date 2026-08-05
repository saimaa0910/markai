"""
Notifications DTO.
"""

from dataclasses import dataclass


@dataclass
class NotificationDTO:
    id: str
    title: str
    message: str
