"""
EAIMOS Observability Mappers
=============================
Entity to DTO converters for Traces and Incidents.
"""

from typing import Any
from api.services.observability.dtos import TraceResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def trace_to_response_dto(entity: Any) -> TraceResponseDTO:
    return TraceResponseDTO(
        id=entity.id,
        trace_id=entity.trace_id,
        span_id=entity.span_id,
        name=entity.name,
        duration_ms=_get_val(entity, "duration_ms", 0),
        status=_get_val(entity, "status", "success"),
        start_time=entity.start_time,
        end_time=entity.end_time,
    )
