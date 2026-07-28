"""
EAIMOS Real-time Stream Service (Sprint 10)
============================================
Service Layer managing SSE & WebSocket LLM Token Streaming.
"""

import logging
import uuid
from typing import Any, AsyncGenerator, Optional

from api.services.base import ServiceContext, ServiceResult
from api.services.chat.dtos import StreamChunkDTO

logger = logging.getLogger("eaimos.chat.stream")


class RealtimeStreamService:
    """Real-time Token Stream & AGUI Protocol Service."""

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

    async def stream_completion_chunks(
        self,
        ctx: ServiceContext,
        conversation_id: uuid.UUID,
        prompt_text: str,
    ) -> AsyncGenerator[StreamChunkDTO, None]:
        tokens = ["Hello", " ", "there!", " ", "How", " ", "can", " ", "I", " ", "help?"]
        for i, token in enumerate(tokens):
            finish_reason = "stop" if i == len(tokens) - 1 else None
            yield StreamChunkDTO(
                conversation_id=conversation_id,
                delta_text=token,
                finish_reason=finish_reason,
            )
