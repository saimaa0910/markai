"""
EAIMOS Infrastructure Interfaces
=================================
Protocol declarations for Sprint 12 Infrastructure services.
"""

from typing import Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.infrastructure.dtos import (
    UploadFileAssetDTO,
    FileAssetResponseDTO,
    SendNotificationDTO,
    NotificationResponseDTO,
    CreateFeatureFlagDTO,
    FeatureFlagResponseDTO,
)


class IFileStorageService(Protocol):
    async def upload_file(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: UploadFileAssetDTO,
    ) -> ServiceResult[FileAssetResponseDTO]: ...


class INotificationService(Protocol):
    async def send_notification(
        self,
        ctx: ServiceContext,
        dto: SendNotificationDTO,
    ) -> ServiceResult[NotificationResponseDTO]: ...


class IFeatureFlagService(Protocol):
    async def create_flag(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateFeatureFlagDTO,
    ) -> ServiceResult[FeatureFlagResponseDTO]: ...

    async def evaluate_flag(
        self,
        ctx: ServiceContext,
        flag_key: str,
    ) -> ServiceResult[bool]: ...
