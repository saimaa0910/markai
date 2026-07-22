"""
EAIMOS Pagination Primitives
=============================
Offset and Cursor pagination primitives for the Repository Layer.
"""

import base64
import json
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class OffsetParams(BaseModel):
    """Parameters for offset-based pagination."""

    page: int = Field(default=1, ge=1, description="1-based page index")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        return self.page_size


class CursorParams(BaseModel):
    """Parameters for keyset cursor pagination."""

    cursor: Optional[str] = Field(default=None, description="Opaque base64 encoded cursor token")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_field: str = Field(default="created_at", description="Field name for sorting cursor")
    sort_order: str = Field(default="desc", description="Sort order: asc or desc")


class PageResult(BaseModel, Generic[T]):
    """Response payload for offset paginated queries."""

    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        params: OffsetParams,
    ) -> "PageResult[T]":
        total_pages = (total + params.page_size - 1) // params.page_size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
            has_next=params.page < total_pages,
            has_previous=params.page > 1,
        )


class CursorResult(BaseModel, Generic[T]):
    """Response payload for cursor paginated queries."""

    items: List[Any]
    next_cursor: Optional[str] = None
    previous_cursor: Optional[str] = None
    has_more: bool = False

    @staticmethod
    def encode_cursor(values: Dict[str, Any]) -> str:
        """Encode cursor dict values into opaque base64 string."""
        serialized = json.dumps(values, default=str)
        return base64.urlsafe_b64encode(serialized.encode("utf-8")).decode("utf-8")

    @staticmethod
    def decode_cursor(cursor_str: str) -> Dict[str, Any]:
        """Decode base64 opaque cursor token into values dict."""
        try:
            decoded_bytes = base64.urlsafe_b64decode(cursor_str.encode("utf-8"))
            return json.loads(decoded_bytes.decode("utf-8"))
        except Exception as exc:
            raise ValueError(f"Invalid pagination cursor token: {exc}") from exc
