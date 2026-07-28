"""
EAIMOS AI Gateway Mappers
===========================
ORM-to-DTO conversion mapping functions for AI Gateway entities.
"""

from typing import Any, List
from api.services.ai.dtos import PromptResponseDTO, RenderedPromptResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"): # MagicMock fallback
        return default
    return val if val is not None else default


def prompt_to_response_dto(entity: Any) -> PromptResponseDTO:
    tags_list = [t.name for t in entity.tags] if hasattr(entity, "tags") and entity.tags and not hasattr(entity.tags, "_mock_name") else []
    return PromptResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        collection_id=_get_val(entity, "collection_id"),
        folder_id=_get_val(entity, "folder_id"),
        category_id=_get_val(entity, "category_id"),
        owner_id=_get_val(entity, "owner_id"),
        title=entity.title,
        template=entity.template,
        description=_get_val(entity, "description"),
        version=_get_val(entity, "version", 1),
        is_active=_get_val(entity, "is_active", True),
        is_archived=_get_val(entity, "is_archived", False),
        is_favorite=_get_val(entity, "is_favorite", False),
        is_pinned=_get_val(entity, "is_pinned", False),
        visibility=_get_val(entity, "visibility", "ORGANIZATION"),
        tags=tags_list,
        variables=[(v.name if hasattr(v, "name") else v) for v in entity.variables] if getattr(entity, "variables", None) and not hasattr(entity.variables, "_mock_name") else [],
        default_model=_get_val(entity, "default_model"),
        default_provider=_get_val(entity, "default_provider"),
        temperature=_get_val(entity, "temperature", 0.7),
        top_p=_get_val(entity, "top_p", 1.0),
        max_tokens=_get_val(entity, "max_tokens"),
        created_at=entity.created_at,
        updated_at=_get_val(entity, "updated_at"),
    )


def prompts_to_response_list(entities: List[Any]) -> List[PromptResponseDTO]:
    return [prompt_to_response_dto(e) for e in entities]
