"""
Notifications Repository.
"""

from typing import List, Any


class NotificationRepository:
    async def get_user_notifications(self, user_id: str) -> List[Any]:
        return []


notification_repository = NotificationRepository()
