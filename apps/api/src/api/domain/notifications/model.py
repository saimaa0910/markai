"""
Notifications Model Entity.
"""

from pydantic import BaseModel


class NotificationDomainEntity(BaseModel):
    id: str
    user_id: str
    title: str
    message: str
    is_read: bool = False
