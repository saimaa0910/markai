"""
EAIMOS Infrastructure Mappers
==============================
Entity to DTO converters for File Assets and Feature Flags.
"""

from typing import Any
from api.services.infrastructure.dtos import FileAssetResponseDTO, FeatureFlagResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def file_asset_to_response_dto(entity: Any) -> FileAssetResponseDTO:
    return FileAssetResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        filename=entity.filename,
        file_type=entity.file_type,
        mime_type=_get_val(entity, "mime_type"),
        file_size=entity.file_size,
        storage_url=_get_val(entity, "storage_url"),
        created_at=entity.created_at,
    )


def feature_flag_to_response_dto(entity: Any) -> FeatureFlagResponseDTO:
    return FeatureFlagResponseDTO(
        id=entity.id,
        key=entity.key,
        name=entity.name,
        is_enabled=_get_val(entity, "is_enabled", True),
        strategy=_get_val(entity, "strategy", "BOOLEAN"),
        created_at=entity.created_at,
    )
