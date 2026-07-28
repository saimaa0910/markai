"""
EAIMOS Chat Dependencies
========================
FastAPI dependency providers for Sprint 10 Chat services.
"""

from api.services.base.dependency_provider import container
from api.services.chat.chat_conversation_service import ChatConversationService
from api.services.chat.chat_message_service import ChatMessageService
from api.services.chat.realtime_stream_service import RealtimeStreamService


def get_chat_conversation_service() -> ChatConversationService:
    return ChatConversationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_chat_message_service() -> ChatMessageService:
    return ChatMessageService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_realtime_stream_service() -> RealtimeStreamService:
    return RealtimeStreamService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
