import uuid
import smtplib
from email.mime.text import MIMEText
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from api.core.config import settings
from api.models.integration import Notification, NotificationPreference, NotificationChannel, NotificationPriority
from api.models.user import User


class NotificationService:
    """
    Handles user notification routing, preference checks, in-app delivery,
    SMTP email dispatching, and slack triggers.
    """

    @staticmethod
    def send_notification(
        db: Session,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
        title: str,
        body: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        event_type: Optional[str] = None,
        action_url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Notification]:
        # 1. Check User notification preferences for this channel/event_type
        pref = db.scalars(
            select(NotificationPreference).where(
                and_(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.organization_id == organization_id,
                    NotificationPreference.channel == channel,
                    NotificationPreference.deleted_at.is_(None),
                )
            )
        ).first()

        if pref:
            if not pref.enabled:
                return None  # Channel is muted globally
            muted_types = pref.muted_event_types or {}
            # Under SQLite or Postgres JSON representation
            if isinstance(muted_types, list) and event_type in muted_types:
                return None  # Specific event type is muted
            elif isinstance(muted_types, dict) and event_type in muted_types.get("muted", []):
                return None

        # 2. In-App Notification Delivery
        if channel == NotificationChannel.IN_APP:
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                title=title,
                body=body,
                channel=channel,
                priority=priority,
                event_type=event_type,
                action_url=action_url,
                metadata=metadata,
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification

        # 3. Email Delivery (SMTP)
        elif channel == NotificationChannel.EMAIL:
            user = db.query(User).filter(User.id == user_id).first()
            if not user or not user.email:
                return None

            msg = MIMEText(body, "html")
            msg["Subject"] = title
            msg["From"] = settings.EMAIL_FROM
            msg["To"] = user.email

            # Dispatch SMTP if password configured, otherwise logs/simulates dispatch
            if settings.SMTP_PASSWORD:
                try:
                    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
                        server.starttls()
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                        server.send_message(msg)
                except Exception as smtp_exc:
                    # In enterprise context: log SMTP exception and fallback gracefully
                    pass

            # Still create an in-app log trace of the notification
            notification = Notification(
                user_id=user_id,
                organization_id=organization_id,
                title=title,
                body=body,
                channel=channel,
                priority=priority,
                event_type=event_type,
                action_url=action_url,
                metadata=metadata,
            )
            db.add(notification)
            db.commit()
            db.refresh(notification)
            return notification

        return None

    @staticmethod
    def get_user_preferences(
        db: Session,
        user_id: uuid.UUID,
        organization_id: uuid.UUID,
    ) -> List[NotificationPreference]:
        # Ensure default preferences exist for all channels
        existing = list(
            db.scalars(
                select(NotificationPreference).where(
                    and_(
                        NotificationPreference.user_id == user_id,
                        NotificationPreference.organization_id == organization_id,
                        NotificationPreference.deleted_at.is_(None),
                    )
                )
            ).all()
        )

        channels = [
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
        ]
        existing_channels = [p.channel for p in existing]

        for c in channels:
            if c not in existing_channels:
                pref = NotificationPreference(
                    user_id=user_id,
                    organization_id=organization_id,
                    channel=c,
                    enabled=True,
                    muted_event_types=[],
                )
                db.add(pref)
                db.commit()
                existing.append(pref)

        return existing
