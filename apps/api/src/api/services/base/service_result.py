"""
EAIMOS Service Result Module
============================
Encapsulates service response payload, success status, detailed validation & business errors,
semantic status codes, warnings, and metadata across the Service Layer.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar
from dataclasses import dataclass, field

T = TypeVar("T")


@dataclass
class ServiceResult(Generic[T]):
    """
    Standard outcome object returned by all service operations.
    Fully framework-independent while supporting semantic error codes and metadata.
    """

    success: bool
    data: Optional[T] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error_code: Optional[str] = None
    status_code: int = 200

    @property
    def is_success(self) -> bool:
        """True if operation completed successfully."""
        return self.success

    @property
    def is_failure(self) -> bool:
        """True if operation failed."""
        return not self.success

    def __bool__(self) -> bool:
        """Allows direct truthiness evaluation in pythonic code: `if result:`."""
        return self.success

    def unwrap(self) -> T:
        """
        Unwrap data if successful, otherwise raise a ServiceError with result details.
        """
        if not self.success:
            from api.services.base.service_exceptions import ServiceError
            err_msg = self.errors[0] if self.errors else "Service operation failed"
            raise ServiceError(
                message=err_msg,
                error_code=self.error_code or "SERVICE_ERROR",
                status_code=self.status_code,
                details={"errors": self.errors, "metadata": self.metadata},
            )
        if self.data is None:
            raise ValueError("ServiceResult completed successfully but returned no data.")
        return self.data

    @classmethod
    def ok(
        cls,
        data: Optional[T] = None,
        metadata: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        status_code: int = 200,
    ) -> "ServiceResult[T]":
        """Factory method for successful service execution."""
        return cls(
            success=True,
            data=data,
            errors=[],
            warnings=warnings or [],
            metadata=metadata or {},
            error_code=None,
            status_code=status_code,
        )

    @classmethod
    def fail(
        cls,
        error: str,
        error_code: Optional[str] = "SERVICE_ERROR",
        status_code: int = 400,
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
    ) -> "ServiceResult[T]":
        """Factory method for failed service execution."""
        all_errors = [error]
        if errors:
            all_errors.extend([e for e in errors if e != error])
        return cls(
            success=False,
            data=None,
            errors=all_errors,
            warnings=warnings or [],
            metadata=metadata or {},
            error_code=error_code,
            status_code=status_code,
        )

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        error_code: Optional[str] = None,
        status_code: int = 500,
    ) -> "ServiceResult[T]":
        """Factory method to construct a failed ServiceResult from an exception."""
        from api.services.base.service_exceptions import ServiceError
        if isinstance(exc, ServiceError):
            return cls(
                success=False,
                data=None,
                errors=[exc.message],
                metadata=exc.details or {},
                error_code=exc.error_code,
                status_code=exc.status_code,
            )
        return cls(
            success=False,
            data=None,
            errors=[str(exc)],
            metadata={"exception_type": exc.__class__.__name__},
            error_code=error_code or "INTERNAL_SERVICE_ERROR",
            status_code=status_code,
        )

    def to_exception(self):
        """Convert a failed ServiceResult to a FastAPI HTTPException."""
        from fastapi import HTTPException
        err_msg = self.errors[0] if self.errors else "Service operation failed"
        return HTTPException(
            status_code=self.status_code,
            detail=err_msg,
        )
