"""
Shared utility schemas used across the entire Viptant API.
Includes paginated response envelopes and standard API response wrappers.
"""
from typing import Generic, List, TypeVar, Optional
from pydantic import BaseModel

DataType = TypeVar("DataType")


class PaginatedResponse(BaseModel, Generic[DataType]):
    """
    Standard paginated response envelope.
    All list endpoints should return this shape for consistency.
    """
    items: List[DataType]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool

    @classmethod
    def build(
        cls,
        items: List[DataType],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[DataType]":
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_prev=page > 1,
        )


class APIResponse(BaseModel, Generic[DataType]):
    """
    Standard single-resource API response envelope.
    """
    success: bool = True
    data: Optional[DataType] = None
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    field: Optional[str] = None


class ErrorResponse(BaseModel):
    success: bool = False
    error: ErrorDetail
