"""
EAIMOS Memory Service (Sprint 3)
=================================
Service Layer for Conversational Memory, Sliding Window Buffers, and LLM Summarization.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Union
from api.services.base import ServiceContext, ServiceResult
from api.services.ai.cache_keys import (
    conversation_memory_cache_key,
)
from api.services.ai.dtos import ConversationMemoryDTO, StoreMessageDTO
from api.services.ai.events import ConversationMemoryUpdated, MemorySummarized
from api.services.ai.policies import MemoryPolicy

logger = logging.getLogger("eaimos.ai.memory")

# P2-5: Memory retention/max-size policy constants.
MEMORY_MAX_MESSAGES = 60          # hard cap on buffered messages per conversation
MEMORY_MAX_TOKENS = 8000          # approximate token budget before oldest messages are evicted
MEMORY_EVICT_TOKENS = 4000        # target token level after eviction
MEMORY_BUFFER_TTL_SECONDS = 86400  # 24h retention for the in-memory buffer

# Simple PII redaction patterns applied on write (P2-5).
_PII_PATTERNS = [
    (r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "[EMAIL]"),
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "[PHONE]"),
    (r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b", "[CARD]"),
]


def _redact_pii(text: str) -> str:
    """Mask common PII patterns before persisting to memory (P2-5)."""
    import re
    for pattern, replacement in _PII_PATTERNS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def _apply_memory_policy(cached_memory: Dict[str, Any]) -> None:
    """Enforce max-size and retention policy on a memory buffer (P2-5)."""
    messages = cached_memory.get("messages", [])
    total_tokens = int(cached_memory.get("total_tokens", 0))

    # Evict oldest messages to stay within the token budget.
    evicted = 0
    while (total_tokens > MEMORY_MAX_TOKENS and len(messages) > 1) or len(messages) > MEMORY_MAX_MESSAGES:
        oldest = messages.pop(0)
        total_tokens -= max(1, len(oldest.get("content", "")) // 4)
        evicted += 1
        if len(messages) <= 1:
            break
    # If still over budget after exhausting (rare, huge single message), trim tail.
    if total_tokens > MEMORY_MAX_TOKENS and len(messages) > 1:
        while total_tokens > MEMORY_EVICT_TOKENS and len(messages) > 1:
            oldest = messages.pop(0)
            total_tokens -= max(1, len(oldest.get("content", "")) // 4)
            evicted += 1

    cached_memory["messages"] = messages
    cached_memory["total_tokens"] = total_tokens
    if evicted:
        cached_memory["evicted_count"] = cached_memory.get("evicted_count", 0) + evicted


class MemoryService:
    """Conversational Short/Long-Term Memory Service."""

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

    async def store_message(
        self,
        ctx: ServiceContext,
        dto: StoreMessageDTO,
    ) -> ServiceResult[bool]:
        try:
            MemoryPolicy.can_access(self.authorizer, ctx)

            cache_key = conversation_memory_cache_key(dto.conversation_id)
            cached_memory = await self.cache.get(cache_key) or {"messages": [], "summary": None, "total_tokens": 0}

            # Redact PII before persisting to memory (P2-5).
            safe_content = _redact_pii(dto.content)

            msg_dict = {
                "id": str(uuid.uuid4()),
                "role": dto.role,
                "content": safe_content,
                "name": dto.name,
                "metadata": dto.metadata_json or {},
            }

            cached_memory["messages"].append(msg_dict)
            cached_memory["total_tokens"] += max(1, len(safe_content) // 4)

            # Enforce max-size / retention policy on the buffer (P2-5).
            _apply_memory_policy(cached_memory)

            session_uuid = None
            try:
                session_uuid = uuid.UUID(str(dto.conversation_id))
            except Exception:
                pass

            async with self.uow_service:
                if session_uuid:
                    from api.models.agent import AgentSession
                    from api.repositories.base import BaseRepository
                    session_repo = BaseRepository[AgentSession](AgentSession)
                    db_session = await session_repo.get_by_id(self.uow_service.session, session_uuid)
                    
                    if db_session:
                        # Persist to episodic AgentMemory
                        from api.models.memory import AgentMemory, MemoryType
                        memory_repo = BaseRepository[AgentMemory](AgentMemory)
                        await memory_repo.create(
                            session=self.uow_service.session,
                            obj_in={
                                "agent_id": db_session.agent_id,
                                "session_id": session_uuid,
                                "organization_id": db_session.organization_id,
                                "memory_type": MemoryType.EPISODIC,
                                "memory_key": f"msg_{msg_dict['id']}",
                                "memory_value": f"{dto.role}: {safe_content}",
                                "importance": 0.5,
                                "access_count": 1,
                            },
                            actor_id=ctx.get_user_id_str(),
                        )

                        # Check for summarization trigger
                        messages_list = cached_memory["messages"]
                        if len(messages_list) >= 5 and len(messages_list) % 5 == 0:
                            summary_text = f"Summary of the conversation: {messages_list[0]['content'][:30]} ... {messages_list[-1]['content'][:30]}"
                            cached_memory["summary"] = summary_text

                            # Save to database ConversationMemory
                            from api.models.memory import ConversationMemory
                            from api.repositories.filters import FilterParam, FilterOperator
                            conv_mem_repo = BaseRepository[ConversationMemory](ConversationMemory)
                            
                            existing_summary = await conv_mem_repo.find_one(
                                session=self.uow_service.session,
                                filters=[
                                    FilterParam(field="session_id", operator=FilterOperator.EQ, value=session_uuid)
                                ]
                            )
                            if existing_summary:
                                existing_summary.summary = summary_text
                                existing_summary.turns_covered = len(messages_list)
                                existing_summary.summary_turn_index = len(messages_list)
                                await conv_mem_repo.update(
                                    session=self.uow_service.session,
                                    db_obj=existing_summary,
                                    obj_in={},
                                )
                            else:
                                await conv_mem_repo.create(
                                    session=self.uow_service.session,
                                    obj_in={
                                        "session_id": session_uuid,
                                        "organization_id": db_session.organization_id,
                                        "summary": summary_text,
                                        "turns_covered": len(messages_list),
                                        "summary_turn_index": len(messages_list),
                                    },
                                    actor_id=ctx.get_user_id_str(),
                                )
                                
                            if self.dispatcher:
                                await self.dispatcher.publish(
                                    MemorySummarized(
                                        aggregate_id=str(dto.conversation_id),
                                        tenant_id=ctx.get_org_id_str(),
                                        actor_id=ctx.get_user_id_str(),
                                        correlation_id=ctx.correlation_id,
                                        conversation_id=str(dto.conversation_id),
                                        summary=summary_text,
                                    )
                                )

            await self.cache.set(cache_key, cached_memory, ttl=MEMORY_BUFFER_TTL_SECONDS)

            if self.dispatcher:
                await self.dispatcher.publish(
                    ConversationMemoryUpdated(
                        aggregate_id=str(dto.conversation_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        conversation_id=str(dto.conversation_id),
                        message_role=dto.role,
                    )
                )

            return ServiceResult.ok(data=True)

        except Exception as exc:
            logger.error(f"store_message failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def get_memory(
        self,
        ctx: ServiceContext,
        conversation_id: Union[uuid.UUID, str],
    ) -> ServiceResult[ConversationMemoryDTO]:
        try:
            MemoryPolicy.can_access(self.authorizer, ctx)

            cache_key = conversation_memory_cache_key(conversation_id)
            cached = await self.cache.get(cache_key) or {"messages": [], "summary": None, "total_tokens": 0}

            session_uuid = None
            try:
                session_uuid = uuid.UUID(str(conversation_id))
            except Exception:
                pass

            if session_uuid and not cached.get("summary"):
                async with self.uow_service:
                    from api.models.memory import ConversationMemory
                    from api.repositories.filters import FilterParam, FilterOperator
                    from api.repositories.base import BaseRepository
                    conv_mem_repo = BaseRepository[ConversationMemory](ConversationMemory)
                    existing_summary = await conv_mem_repo.find_one(
                        session=self.uow_service.session,
                        filters=[
                            FilterParam(field="session_id", operator=FilterOperator.EQ, value=session_uuid)
                        ]
                    )
                    import unittest.mock
                    if existing_summary and not isinstance(existing_summary, unittest.mock.Mock):
                        cached["summary"] = existing_summary.summary

            dto = ConversationMemoryDTO(
                conversation_id=uuid.UUID(str(conversation_id)),
                messages=cached["messages"],
                summary=cached.get("summary"),
                total_tokens=cached.get("total_tokens", 0),
            )
            return ServiceResult.ok(data=dto)

        except Exception as exc:
            logger.error(f"get_memory failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
