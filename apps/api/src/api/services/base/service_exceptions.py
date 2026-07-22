"""
EAIMOS Service Exceptions Module
================================
Defines strict, enterprise exception hierarchy for the Service Layer.
All service exceptions derive from ServiceError and provide structured error metadata,
semantic error codes, and HTTP-compatible status codes without depending on FastAPI.
"""

from typing import Any, Dict, List, Optional


class ServiceError(Exception):
    """Base exception for all domain and service layer errors in EAIMOS."""

    def __init__(
        self,
        message: str,
        error_code: str = "SERVICE_ERROR",
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """Serialize exception into a structured dictionary."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
            "details": self.details,
        }


class ValidationError(ServiceError):
    """Raised when input DTOs, parameters, or field constraints fail validation."""

    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: Optional[List[Dict[str, Any]]] = None,
        error_code: str = "VALIDATION_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_details = details or {}
        if field_errors:
            merged_details["field_errors"] = field_errors
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=422,
            details=merged_details,
        )
        self.field_errors = field_errors or []


class BusinessRuleViolation(ServiceError):
    """Raised when an operation violates a domain business rule or invariant."""

    def __init__(
        self,
        message: str,
        rule_name: Optional[str] = None,
        error_code: str = "BUSINESS_RULE_VIOLATION",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_details = details or {}
        if rule_name:
            merged_details["rule_name"] = rule_name
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=merged_details,
        )


class UnauthorizedOperation(ServiceError):
    """Raised when unauthenticated or missing identity context prevents operation."""

    def __init__(
        self,
        message: str = "Authentication required for this operation",
        error_code: str = "UNAUTHORIZED",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class ForbiddenOperation(ServiceError):
    """Raised when actor lacks required permissions, roles, or tenant access."""

    def __init__(
        self,
        message: str = "Permission denied for this operation",
        required_permissions: Optional[List[str]] = None,
        error_code: str = "FORBIDDEN",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_details = details or {}
        if required_permissions:
            merged_details["required_permissions"] = required_permissions
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=403,
            details=merged_details,
        )


class ConflictError(ServiceError):
    """Raised when operation conflicts with current state of resource (e.g. concurrency)."""

    def __init__(
        self,
        message: str = "Resource state conflict",
        error_code: str = "RESOURCE_CONFLICT",
        status_code: int = 409,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
        )


class AlreadyExistsError(ConflictError):
    """Raised when attempting to create an entity that already exists."""

    def __init__(
        self,
        message: str = "Entity already exists",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: str = "ALREADY_EXISTS",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_details = details or {}
        if resource_type:
            merged_details["resource_type"] = resource_type
        if resource_id:
            merged_details["resource_id"] = resource_id
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=409,
            details=merged_details,
        )


class NotFoundError(ServiceError):
    """Raised when requested entity or resource cannot be located."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        error_code: str = "NOT_FOUND",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_details = details or {}
        if resource_type:
            merged_details["resource_type"] = resource_type
        if resource_id:
            merged_details["resource_id"] = resource_id
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=404,
            details=merged_details,
        )


class ExternalServiceError(ServiceError):
    """Raised when an external downstream dependency (AI API, Redis, RabbitMQ) fails."""

    def __init__(
        self,
        message: str = "External service integration failed",
        service_name: Optional[str] = None,
        error_code: str = "EXTERNAL_SERVICE_ERROR",
        status_code: int = 502,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        merged_details = details or {}
        if service_name:
            merged_details["service_name"] = service_name
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=merged_details,
        )
