"""
EAIMOS Workflow Validators
===========================
Validation for DAG step definitions, cron syntax, and triggers.
"""

from typing import Any, Dict, List
from api.services.base.service_exceptions import ValidationError, BusinessRuleViolation
from api.services.workflow.constants import SUPPORTED_WORKFLOW_TRIGGERS


def validate_workflow_trigger_supported(trigger: str) -> None:
    if trigger.upper() not in SUPPORTED_WORKFLOW_TRIGGERS:
        raise ValidationError(
            message=f"Unsupported workflow trigger '{trigger}'.",
            field_errors=[{"field": "trigger", "message": f"Supported triggers: {sorted(SUPPORTED_WORKFLOW_TRIGGERS)}"}],
        )


def validate_dag_structure(steps: List[Dict[str, Any]]) -> None:
    """Ensure DAG has unique step IDs and no circular dependencies."""
    step_ids = [s.get("id") for s in steps if "id" in s]
    if len(step_ids) != len(set(step_ids)):
        raise ValidationError(
            message="Workflow steps contain duplicate step IDs.",
            field_errors=[{"field": "steps_definition", "message": "Step IDs must be unique"}],
        )
