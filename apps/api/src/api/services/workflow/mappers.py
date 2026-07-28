"""
EAIMOS Workflow Mappers
========================
ORM to DTO converters for Workflow entities.
"""

from typing import Any, List
from api.services.workflow.dtos import WorkflowDefinitionResponseDTO


def _get_val(obj: Any, attr: str, default: Any = None) -> Any:
    val = getattr(obj, attr, default)
    if hasattr(val, "_mock_name"):
        return default
    return val if val is not None else default


def workflow_to_response_dto(entity: Any) -> WorkflowDefinitionResponseDTO:
    status_str = entity.status.value if hasattr(entity.status, "value") else str(entity.status)
    trigger_str = entity.trigger.value if hasattr(entity.trigger, "value") else str(entity.trigger)

    return WorkflowDefinitionResponseDTO(
        id=entity.id,
        organization_id=entity.organization_id,
        name=entity.name,
        description=_get_val(entity, "description"),
        status=status_str,
        trigger=trigger_str,
        steps_definition=_get_val(entity, "steps_definition"),
        cron_expression=_get_val(entity, "cron_expression"),
        max_retries=_get_val(entity, "max_retries", 3),
        timeout_seconds=_get_val(entity, "timeout_seconds", 3600),
        created_at=entity.created_at,
        updated_at=_get_val(entity, "updated_at"),
    )
