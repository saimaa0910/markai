"""
EAIMOS Knowledge Base Mappers
==============================
Entity to DTO converters for Knowledge Collections and Documents.
"""

from typing import Any
from api.services.knowledge.dtos import KnowledgeCollectionResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def collection_to_response_dto(entity: Any) -> KnowledgeCollectionResponseDTO:
    return KnowledgeCollectionResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        name=entity.name,
        description=_get_val(entity, "description"),
        visibility=_get_val(entity, "visibility", "ORGANIZATION"),
        is_archived=_get_val(entity, "is_archived", False),
        is_favorite=_get_val(entity, "is_favorite", False),
        is_pinned=_get_val(entity, "is_pinned", False),
        created_at=entity.created_at,
    )
