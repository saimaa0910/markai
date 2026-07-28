"""
Sprint 10 Conversational AI & Real-time Messaging Service Tests
==================================================================
Tests for ChatConversationService, ChatMessageService, and RealtimeStreamService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.chat.chat_conversation_service import ChatConversationService
from api.services.chat.chat_message_service import ChatMessageService
from api.services.chat.realtime_stream_service import RealtimeStreamService
from api.services.chat.dtos import (
    CreateConversationDTO,
    SendMessageDTO,
)


def make_ctx() -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer() -> MagicMock:
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = True
    return auth


def make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = MagicMock()
    uow.add_event = MagicMock()
    return uow


def make_entity(**kwargs) -> MagicMock:
    entity = MagicMock()
    entity.id = kwargs.get("id", uuid.uuid4())
    entity.created_at = datetime.now(timezone.utc)
    for k, v in kwargs.items():
        setattr(entity, k, v)
    return entity


class TestChatConversationService:
    @pytest.mark.asyncio
    async def test_create_conversation(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        conv_entity = make_entity(
            user_id=ctx.user_id,
            organization_id=ctx.organization_id,
            title="Q4 Campaign Copy Assistant",
            system_prompt="You are a senior marketing copywriter.",
            model_name="gemini-2.5-flash",
            provider_name="google",
            temperature=0.7,
            is_archived=False,
            is_favorite=False,
            is_pinned=False,
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = conv_entity

        svc = ChatConversationService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.chat.chat_conversation_service._ConversationRepository", return_value=repo_mock):
            res = await svc.create_conversation(
                ctx,
                org_id=ctx.organization_id,
                dto=CreateConversationDTO(
                    title="Q4 Campaign Copy Assistant",
                    system_prompt="You are a senior marketing copywriter.",
                ),
            )

        assert res.is_success
        assert res.data.title == "Q4 Campaign Copy Assistant"


class TestChatMessageService:
    @pytest.mark.asyncio
    async def test_send_message(self):
        ctx = make_ctx()
        authorizer = make_authorizer()

        svc = ChatMessageService(authorizer=authorizer)
        res = await svc.send_message(
            ctx,
            dto=SendMessageDTO(
                conversation_id=uuid.uuid4(),
                role="USER",
                content="Draft an email for product launch.",
            ),
        )

        assert res.is_success
        assert res.data.role == "USER"
        assert res.data.token_count > 0


class TestRealtimeStreamService:
    @pytest.mark.asyncio
    async def test_stream_completion_chunks(self):
        ctx = make_ctx()
        svc = RealtimeStreamService()

        chunks = []
        async for chunk in svc.stream_completion_chunks(ctx, conversation_id=uuid.uuid4(), prompt_text="Hello"):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert chunks[-1].finish_reason == "stop"
