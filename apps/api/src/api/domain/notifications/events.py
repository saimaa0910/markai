"""
Notifications Events.
"""

from dataclasses import dataclass


@dataclass
class NotificationSentEvent:
    notification_id: str
    user_id: str
