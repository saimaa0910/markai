"""
EAIMOS Enterprise Validators Module
====================================
Provides reusable validation rules, constraint checkers, and a fluent ValidatorChain
to validate DTOs, cross-field integrity, tenant scoping, reference existence, and duplicate rules.
"""

from typing import Any, Awaitable, Callable, Dict, List, Optional, Sequence, Union
import uuid

from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import ValidationError


def validate_required(value: Any, field_name: str) -> Optional[Dict[str, Any]]:
    """Validate that a field value is not None, empty string, or empty container."""
    if value is None or (isinstance(value, (str, list, dict, set, tuple)) and len(value) == 0):
        return {
            "field": field_name,
            "message": f"Field '{field_name}' is required and cannot be empty.",
            "error_code": "FIELD_REQUIRED",
        }
    return None


def validate_business_rule(
    condition: bool,
    rule_name: str,
    message: str,
    field_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Validate a boolean business condition; return error dict if condition is False."""
    if not condition:
        return {
            "field": field_name or "general",
            "message": message,
            "rule_name": rule_name,
            "error_code": "BUSINESS_RULE_VIOLATION",
        }
    return None


def validate_cross_fields(
    field_a_name: str,
    field_a_val: Any,
    field_b_name: str,
    field_b_val: Any,
    validator_func: Callable[[Any, Any], bool],
    message: str,
) -> Optional[Dict[str, Any]]:
    """Cross-field validation comparing two field values with a custom predicate."""
    if not validator_func(field_a_val, field_b_val):
        return {
            "field": f"{field_a_name},{field_b_name}",
            "message": message,
            "error_code": "CROSS_FIELD_VALIDATION_FAILED",
        }
    return None


class ValidatorChain:
    """
    Fluent validation chain for accumulating field and business constraint errors.
    Supports both sync rule evaluation and async reference/duplicate checks.
    """

    def __init__(self) -> None:
        self.errors: List[Dict[str, Any]] = []

    def add_error(
        self,
        field: str,
        message: str,
        error_code: str = "VALIDATION_ERROR",
        **metadata: Any,
    ) -> "ValidatorChain":
        """Explicitly record a validation error."""
        err = {"field": field, "message": message, "error_code": error_code}
        if metadata:
            err.update(metadata)
        self.errors.append(err)
        return self

    def check_required(self, value: Any, field_name: str) -> "ValidatorChain":
        """Chainable required field checker."""
        err = validate_required(value, field_name)
        if err:
            self.errors.append(err)
        return self

    def check_rule(
        self,
        condition: bool,
        rule_name: str,
        message: str,
        field_name: Optional[str] = None,
    ) -> "ValidatorChain":
        """Chainable business rule checker."""
        err = validate_business_rule(condition, rule_name, message, field_name)
        if err:
            self.errors.append(err)
        return self

    def check_cross_fields(
        self,
        field_a_name: str,
        field_a_val: Any,
        field_b_name: str,
        field_b_val: Any,
        validator_func: Callable[[Any, Any], bool],
        message: str,
    ) -> "ValidatorChain":
        """Chainable cross-field validator."""
        err = validate_cross_fields(
            field_a_name, field_a_val, field_b_name, field_b_val, validator_func, message
        )
        if err:
            self.errors.append(err)
        return self

    async def check_no_duplicate(
        self,
        existence_check_func: Callable[[], Awaitable[bool]],
        field_name: str,
        value: Any,
        message: Optional[str] = None,
    ) -> "ValidatorChain":
        """Async duplicate detection checker."""
        exists = await existence_check_func()
        if exists:
            self.errors.append(
                {
                    "field": field_name,
                    "message": message or f"Value '{value}' for field '{field_name}' already exists.",
                    "error_code": "DUPLICATE_VALUE",
                }
            )
        return self

    async def check_reference_exists(
        self,
        existence_check_func: Callable[[], Awaitable[bool]],
        field_name: str,
        ref_id: Any,
        resource_name: str = "Reference",
    ) -> "ValidatorChain":
        """Async reference/foreign-key existence checker."""
        exists = await existence_check_func()
        if not exists:
            self.errors.append(
                {
                    "field": field_name,
                    "message": f"Referenced {resource_name} with ID '{ref_id}' does not exist.",
                    "error_code": "REFERENCE_NOT_FOUND",
                }
            )
        return self

    def check_tenant_ownership(
        self,
        ctx: ServiceContext,
        target_org_id: Optional[Union[uuid.UUID, str]],
        field_name: str = "organization_id",
    ) -> "ValidatorChain":
        """Validate multi-tenant org ownership matching context."""
        if target_org_id and not ctx.is_tenant_member(target_org_id):
            self.errors.append(
                {
                    "field": field_name,
                    "message": f"Access denied: organization boundary conflict for '{target_org_id}'.",
                    "error_code": "TENANT_BOUNDARY_VIOLATION",
                }
            )
        return self

    @property
    def has_errors(self) -> bool:
        """True if any validation errors accumulated."""
        return len(self.errors) > 0

    def validate_or_raise(self, message: str = "Validation failed") -> None:
        """If any validation errors exist, raise a structured ValidationError."""
        if self.has_errors:
            raise ValidationError(
                message=message,
                field_errors=list(self.errors),
            )
