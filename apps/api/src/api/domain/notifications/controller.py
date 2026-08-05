"""
Notifications Controller.
"""

from typing import Dict, Any


class NotificationController:
    async def send_notification(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "sent"}


notification_controller = NotificationController()
