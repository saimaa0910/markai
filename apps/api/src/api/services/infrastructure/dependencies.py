"""
EAIMOS Infrastructure Dependencies
===================================
FastAPI dependency providers for Sprint 12 Infrastructure services.
"""

from api.services.base.dependency_provider import container
from api.services.infrastructure.file_storage_service import FileStorageService
from api.services.infrastructure.notification_service import NotificationService
from api.services.infrastructure.feature_flag_service import FeatureFlagService


def get_file_storage_service() -> FileStorageService:
    return FileStorageService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_notification_service() -> NotificationService:
    return NotificationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_feature_flag_service() -> FeatureFlagService:
    return FeatureFlagService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
