"""
EAIMOS Infrastructure Service Layer (Sprint 12)
================================================
Public API for File Storage, Notifications & Feature Flags services.
"""

from api.services.infrastructure.file_storage_service import FileStorageService
from api.services.infrastructure.notification_service import NotificationService
from api.services.infrastructure.feature_flag_service import FeatureFlagService

from api.services.infrastructure.dtos import (
    UploadFileAssetDTO,
    FileAssetResponseDTO,
    SendNotificationDTO,
    NotificationResponseDTO,
    CreateFeatureFlagDTO,
    FeatureFlagResponseDTO,
)

from api.services.infrastructure.events import (
    FileAssetUploaded,
    NotificationDispatched,
    FeatureFlagEvaluated,
)

from api.services.infrastructure.dependencies import (
    get_file_storage_service,
    get_notification_service,
    get_feature_flag_service,
)

__all__ = [
    "FileStorageService",
    "NotificationService",
    "FeatureFlagService",
    "UploadFileAssetDTO",
    "FileAssetResponseDTO",
    "SendNotificationDTO",
    "NotificationResponseDTO",
    "CreateFeatureFlagDTO",
    "FeatureFlagResponseDTO",
    "FileAssetUploaded",
    "NotificationDispatched",
    "FeatureFlagEvaluated",
    "get_file_storage_service",
    "get_notification_service",
    "get_feature_flag_service",
]
