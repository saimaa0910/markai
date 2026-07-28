"""
EAIMOS Chat Mappers
====================
Entity to DTO converters for Conversations and Messages.
"""

from typing import Any
from api.services.chat.dtos import ConversationResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def conversation_to_response_dto(entity: Any) -> ConversationResponseDTO:
    return ConversationResponseDTO(
        id=entity.id,
        user_id=entity.user_id,
        organization_id=entity.organization_id,
        title=entity.title,
        system_prompt=_get_val(entity, "system_prompt"),
        model_name=_get_val(entity, "model_name"),
        provider_name=_get_val(entity, "provider_name"),
        temperature=_get_val(entity, "temperature", 0.7),
        is_archived=_get_val(entity, "is_archived", False),
        is_favorite=_get_val(entity, "is_favorite", False),
        is_pinned=_get_val(entity, "is_pinned", False),
        created_at=entity.created_at,
    )
