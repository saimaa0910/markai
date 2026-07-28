"""
EAIMOS Chat Service Layer (Sprint 10)
======================================
Public API for Chat Threads, Messages & Realtime Streaming services.
"""

from api.services.chat.chat_conversation_service import ChatConversationService
from api.services.chat.chat_message_service import ChatMessageService
from api.services.chat.realtime_stream_service import RealtimeStreamService

from api.services.chat.dtos import (
    CreateConversationDTO,
    ConversationResponseDTO,
    SendMessageDTO,
    MessageResponseDTO,
    StreamChunkDTO,
)

from api.services.chat.events import (
    ConversationCreated,
    MessageSent,
    ConversationArchived,
)

from api.services.chat.dependencies import (
    get_chat_conversation_service,
    get_chat_message_service,
    get_realtime_stream_service,
)

__all__ = [
    "ChatConversationService",
    "ChatMessageService",
    "RealtimeStreamService",
    "CreateConversationDTO",
    "ConversationResponseDTO",
    "SendMessageDTO",
    "MessageResponseDTO",
    "StreamChunkDTO",
    "get_chat_conversation_service",
    "get_chat_message_service",
    "get_realtime_stream_service",
]
