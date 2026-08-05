"""
Notifications Domain Service — Business Logic Delegation.
Delegates to existing NotificationService implementation.
"""

import uuid
from typing import List, Any
from sqlalchemy.orm import Session
from api.services.notification_service import NotificationService as BaseNotificationService
from api.models.integration import Notification


class NotificationDomainService:
    def list_user_notifications(self, db: Session, user_id: uuid.UUID) -> List[Notification]:
        return db.query(Notification).filter(Notification.user_id == user_id, Notification.deleted_at == None).all()

    def mark_as_read(self, db: Session, notification_id: uuid.UUID, user_id: uuid.UUID) -> Any:
        return BaseNotificationService.mark_read(db, notification_id=notification_id, user_id=user_id)


notification_domain_service = NotificationDomainService()
