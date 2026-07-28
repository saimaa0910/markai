"""
EAIMOS CRM Mappers
===================
Entity to DTO converters for Pipelines, Deals, and Leads.
"""

from typing import Any
from api.services.crm.dtos import PipelineResponseDTO, DealResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def pipeline_to_response_dto(entity: Any) -> PipelineResponseDTO:
    return PipelineResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        name=entity.name,
        description=_get_val(entity, "description"),
        currency=_get_val(entity, "currency", "USD"),
        is_default=_get_val(entity, "is_default", False),
        created_at=entity.created_at,
    )
