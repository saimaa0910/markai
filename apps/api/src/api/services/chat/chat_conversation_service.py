"""
EAIMOS Chat Conversation Service (Sprint 10)
==============================================
Service Layer managing Chat Threads, System Prompts, and Model Parameters.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union

from api.models.conversation import Conversation
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.chat.cache_keys import conversation_cache_key
from api.services.chat.dtos import CreateConversationDTO, ConversationResponseDTO
from api.services.chat.events import ConversationCreated
from api.services.chat.mappers import conversation_to_response_dto
from api.services.chat.policies import ChatPolicy

logger = logging.getLogger("eaimos.chat.conversation")


class _ConversationRepository(BaseRepository[Conversation]):
    def __init__(self) -> None:
        super().__init__(Conversation)


class ChatConversationService:
    """Chat Thread Lifecycle Service."""

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

    async def create_conversation(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateConversationDTO,
    ) -> ServiceResult[ConversationResponseDTO]:
        try:
            ChatPolicy.can_access(self.authorizer, ctx, org_id)

            org_uuid = uuid.UUID(str(org_id))
            user_uuid = ctx.get_user_id_uuid()

            async with self.uow_service:
                repo = _ConversationRepository()
                data: Dict[str, Any] = {
                    "organization_id": str(org_uuid),
                    "user_id": str(user_uuid),
                    "title": dto.title,
                    "system_prompt": dto.system_prompt,
                    "model_name": dto.model_name,
                    "provider_name": dto.provider_name,
                    "temperature": dto.temperature,
                    "is_archived": False,
                    "is_favorite": False,
                    "is_pinned": False,
                }

                conv = await repo.create(
                    session=self.uow_service.session,
                    obj_in=data,
                    actor_id=user_uuid,
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        ConversationCreated(
                            aggregate_id=str(conv.id),
                            tenant_id=str(org_id),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            conversation_id=str(conv.id),
                            title=dto.title,
                        )
                    )

            response = conversation_to_response_dto(conv)
            await self.cache.set(conversation_cache_key(conv.id), response.model_dump(mode="json"))
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_conversation failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
