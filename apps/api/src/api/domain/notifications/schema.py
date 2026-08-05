"""
Notifications Pydantic Schemas.
"""

from pydantic import BaseModel


class NotificationResponseSchema(BaseModel):
    id: str
    title: str
    message: str
    is_read: bool
