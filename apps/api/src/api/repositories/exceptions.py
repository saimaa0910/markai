"""
EAIMOS Repository Exceptions
=============================
Domain-specific exceptions for the Enterprise Repository Layer.
No ORM/SQLAlchemy exceptions leak beyond the repository boundary.
"""

from typing import Any, Dict, Optional, Type


class RepositoryError(Exception):
    """Base exception for all repository layer errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class EntityNotFoundError(RepositoryError):
    """Raised when an entity is not found by key or filter."""

    def __init__(
        self,
        entity_name: str,
        identifier: Any,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = f"{entity_name} with identifier '{identifier}' was not found."
        super().__init__(message=message, details=details or {"entity": entity_name, "identifier": identifier})
        self.entity_name = entity_name
        self.identifier = identifier


class DuplicateEntityError(RepositoryError):
    """Raised when a unique constraint or primary key conflict occurs."""

    def __init__(
        self,
        entity_name: str,
        conflict_field: str,
        conflict_value: Any,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        message = f"{entity_name} already exists with {conflict_field}='{conflict_value}'."
        super().__init__(
            message=message,
            details=details or {"entity": entity_name, "field": conflict_field, "value": conflict_value},
        )
        self.entity_name = entity_name
        self.conflict_field = conflict_field
        self.conflict_value = conflict_value


class OptimisticLockError(RepositoryError):
    """Raised when an entity version mismatch is detected on update/delete."""

    def __init__(
        self,
        entity_name: str,
        identifier: Any,
        expected_version: int,
        actual_version: Optional[int] = None,
    ) -> None:
        message = (
            f"Optimistic lock conflict for {entity_name} '{identifier}'. "
            f"Expected version {expected_version}, but found {actual_version}."
        )
        super().__init__(
            message=message,
            details={
                "entity": entity_name,
                "identifier": identifier,
                "expected_version": expected_version,
                "actual_version": actual_version,
            },
        )
        self.entity_name = entity_name
        self.identifier = identifier
        self.expected_version = expected_version
        self.actual_version = actual_version


class TenantViolationError(RepositoryError):
    """Raised when a tenant access boundary or cross-tenant query violation is detected."""

    def __init__(
        self,
        entity_name: str,
        attempted_org_id: Any,
        context_org_id: Any,
    ) -> None:
        message = (
            f"Tenant Isolation Violation: Attempted to access {entity_name} belonging to "
            f"organization '{attempted_org_id}' from context organization '{context_org_id}'."
        )
        super().__init__(
            message=message,
            details={
                "entity": entity_name,
                "attempted_org_id": str(attempted_org_id),
                "context_org_id": str(context_org_id),
            },
        )
        self.entity_name = entity_name
        self.attempted_org_id = attempted_org_id
        self.context_org_id = context_org_id


class DatabaseConstraintError(RepositoryError):
    """Raised when a foreign key or check constraint is violated."""

    def __init__(self, constraint_name: str, original_error: str) -> None:
        message = f"Database constraint violation '{constraint_name}': {original_error}"
        super().__init__(
            message=message,
            details={"constraint_name": constraint_name, "original_error": original_error},
        )
        self.constraint_name = constraint_name
        self.original_error = original_error
