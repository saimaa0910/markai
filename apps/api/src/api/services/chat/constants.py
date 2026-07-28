"""
EAIMOS Chat & Real-time Messaging Constants
============================================
Constants for Sprint 10 Conversational AI & Real-time Messaging Services.
"""

from typing import Set

SUPPORTED_CHAT_ROLES: Set[str] = {"USER", "ASSISTANT", "SYSTEM", "TOOL"}
DEFAULT_TEMPERATURE: float = 0.7
DEFAULT_MAX_TOKENS: int = 4096
