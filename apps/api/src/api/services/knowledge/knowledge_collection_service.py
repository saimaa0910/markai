"""
EAIMOS Knowledge Collection Service (Sprint 8)
==============================================
Service Layer managing Knowledge Base Collections, Folders, and Scoping.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union

from api.models.knowledge import KnowledgeCollection
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.knowledge.cache_keys import collection_cache_key
from api.services.knowledge.dtos import CreateKnowledgeCollectionDTO, KnowledgeCollectionResponseDTO
from api.services.knowledge.events import KnowledgeCollectionCreated
from api.services.knowledge.mappers import collection_to_response_dto
from api.services.knowledge.policies import KnowledgePolicy
from api.services.knowledge.validators import validate_visibility_supported

logger = logging.getLogger("eaimos.knowledge.collection")


class _KnowledgeCollectionRepository(BaseRepository[KnowledgeCollection]):
    def __init__(self) -> None:
        super().__init__(KnowledgeCollection)


class KnowledgeCollectionService:
    """Knowledge Collection Lifecycle Service."""

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

    async def create_collection(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateKnowledgeCollectionDTO,
    ) -> ServiceResult[KnowledgeCollectionResponseDTO]:
        try:
            KnowledgePolicy.can_create_collection(self.authorizer, ctx, org_id)
            validate_visibility_supported(dto.visibility)

            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _KnowledgeCollectionRepository()
                col_data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "name": dto.name,
                    "description": dto.description,
                    "visibility": dto.visibility.upper(),
                    "is_archived": False,
                    "is_favorite": False,
                    "is_pinned": False,
                }

                col = await repo.create(
                    session=self.uow_service.session,
                    obj_in=col_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        KnowledgeCollectionCreated(
                            aggregate_id=str(col.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            collection_id=str(col.id),
                            name=dto.name,
                        )
                    )

            response = collection_to_response_dto(col)
            await self.cache.set(collection_cache_key(col.id), response.model_dump(mode="json"))
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_collection failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
