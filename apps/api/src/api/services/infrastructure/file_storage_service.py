"""
EAIMOS File Storage Service (Sprint 12)
=======================================
Service Layer managing file assets upload, metadata, and tenant boundaries.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union

from api.models.file_asset import FileAsset
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.infrastructure.cache_keys import file_asset_cache_key
from api.services.infrastructure.dtos import UploadFileAssetDTO, FileAssetResponseDTO
from api.services.infrastructure.events import FileAssetUploaded
from api.services.infrastructure.mappers import file_asset_to_response_dto
from api.services.infrastructure.policies import InfrastructurePolicy
from api.services.infrastructure.validators import validate_file_size

logger = logging.getLogger("eaimos.infrastructure.storage")


class _FileAssetRepository(BaseRepository[FileAsset]):
    def __init__(self) -> None:
        super().__init__(FileAsset)


class FileStorageService:
    """Multi-tenant File Asset Storage and Management Service."""

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        authorizer: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
    ) -> None:
        from api.services.base.dependency_provider import container
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache
        self.authorizer = authorizer or container.authorizer
        self.dispatcher = dispatcher or container.dispatcher

    async def upload_file(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: UploadFileAssetDTO,
    ) -> ServiceResult[FileAssetResponseDTO]:
        try:
            InfrastructurePolicy.can_upload_files(self.authorizer, ctx, org_id)
            validate_file_size(dto.file_size)

            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _FileAssetRepository()
                data: Dict[str, Any] = {
                    "organization_id": org_uuid,
                    "filename": dto.filename,
                    "file_type": dto.file_type,
                    "mime_type": dto.mime_type,
                    "file_size": dto.file_size,
                    "storage_url": dto.storage_url or f"s3://eaimos-tenant-{org_id}/files/{uuid.uuid4()}-{dto.filename}",
                }

                file_entity = await repo.create(
                    session=self.uow_service.session,
                    obj_in=data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        FileAssetUploaded(
                            aggregate_id=str(file_entity.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            file_id=str(file_entity.id),
                            filename=dto.filename,
                            file_size=dto.file_size,
                        )
                    )

            response = file_asset_to_response_dto(file_entity)
            await self.cache.set(file_asset_cache_key(file_entity.id), response.model_dump(mode="json"))
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"upload_file failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
