"""
EAIMOS Chat Message Service (Sprint 10)
========================================
Service Layer managing Message History, Token Counts, and Context Windows.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from api.services.base import ServiceContext, ServiceResult
from api.services.chat.dtos import MessageResponseDTO, SendMessageDTO
from api.services.chat.events import MessageSent
from api.services.chat.validators import validate_chat_role_supported

logger = logging.getLogger("eaimos.chat.message")


class ChatMessageService:
    """Chat Message History & Token Telemetry Service."""

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

    async def send_message(
        self,
        ctx: ServiceContext,
        dto: SendMessageDTO,
    ) -> ServiceResult[MessageResponseDTO]:
        try:
            validate_chat_role_supported(dto.role)
            msg_id = uuid.uuid4()
            estimated_tokens = max(1, len(dto.content) // 4)

            res_dto = MessageResponseDTO(
                id=msg_id,
                conversation_id=dto.conversation_id,
                role=dto.role.upper(),
                content=dto.content,
                token_count=estimated_tokens,
                created_at=datetime.now(timezone.utc),
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    MessageSent(
                        aggregate_id=str(msg_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        message_id=str(msg_id),
                        conversation_id=str(dto.conversation_id),
                        role=dto.role.upper(),
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"send_message failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
