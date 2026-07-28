"""
EAIMOS Pipeline Service (Sprint 9)
===================================
Service Layer managing Sales Pipelines and Stage Configurations.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union

from api.models.deals import Pipeline
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.crm.cache_keys import pipeline_cache_key
from api.services.crm.dtos import CreatePipelineDTO, PipelineResponseDTO
from api.services.crm.events import PipelineCreated
from api.services.crm.mappers import pipeline_to_response_dto
from api.services.crm.policies import CRMPolicy

logger = logging.getLogger("eaimos.crm.pipeline")


class _PipelineRepository(BaseRepository[Pipeline]):
    def __init__(self) -> None:
        super().__init__(Pipeline)


class PipelineService:
    """Sales Pipeline Configuration & Stage Lifecycle Service."""

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

    async def create_pipeline(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreatePipelineDTO,
    ) -> ServiceResult[PipelineResponseDTO]:
        try:
            CRMPolicy.can_manage_pipeline(self.authorizer, ctx, org_id)

            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _PipelineRepository()
                data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "name": dto.name,
                    "description": dto.description,
                    "currency": dto.currency.upper(),
                    "is_default": dto.is_default,
                }

                pipeline = await repo.create(
                    session=self.uow_service.session,
                    obj_in=data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        PipelineCreated(
                            aggregate_id=str(pipeline.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            pipeline_id=str(pipeline.id),
                            name=dto.name,
                        )
                    )

            response = pipeline_to_response_dto(pipeline)
            await self.cache.set(pipeline_cache_key(pipeline.id), response.model_dump(mode="json"))
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_pipeline failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
