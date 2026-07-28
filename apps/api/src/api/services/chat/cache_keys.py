"""
EAIMOS Chat Cache Keys
=======================
Cache key functions for Conversational AI & Real-time Messaging Services.
"""

from typing import Union
import uuid

CHAT_CACHE_PREFIX: str = "chat"


def conversation_cache_key(conv_id: Union[uuid.UUID, str]) -> str:
    return f"{CHAT_CACHE_PREFIX}:conv:{str(conv_id)}"


def conversation_messages_key(conv_id: Union[uuid.UUID, str]) -> str:
    return f"{CHAT_CACHE_PREFIX}:conv:{str(conv_id)}:msgs"
