"""
EAIMOS Infrastructure Domain Events
====================================
Domain events for Sprint 12 File Storage, Notifications & Feature Flags.
"""

from api.services.base.events import DomainEvent


class FileAssetUploaded(DomainEvent):
    event_type: str = "infrastructure.file_asset_uploaded"
    file_id: str = ""
    filename: str = ""
    file_size: int = 0


class NotificationDispatched(DomainEvent):
    event_type: str = "infrastructure.notification_dispatched"
    recipient: str = ""
    channel: str = ""
    subject: str = ""


class FeatureFlagEvaluated(DomainEvent):
    event_type: str = "infrastructure.feature_flag_evaluated"
    flag_key: str = ""
    is_enabled: bool = False
