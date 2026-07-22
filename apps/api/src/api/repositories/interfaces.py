"""
EAIMOS Repository Interfaces
=============================
Abstract Repository protocols establishing contracts for all EAIMOS data access modules.
Ensures total decoupling between Service/Domain layers and SQLAlchemy ORM.
"""

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    runtime_checkable,
)
import uuid
from api.repositories.filters import FilterParam
from api.repositories.pagination import CursorParams, CursorResult, OffsetParams, PageResult
from api.repositories.sorting import SortParam

T = TypeVar("T")


@runtime_checkable
class IBaseRepository(Protocol, Generic[T]):
    """Generic repository contract for full async lifecycle management."""

    async def get_by_id(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
        include_deleted: bool = False,
    ) -> Optional[T]:
        ...

    async def get_by_ids(
        self,
        session: Any,
        ids: Sequence[Union[uuid.UUID, str]],
        include_deleted: bool = False,
    ) -> List[T]:
        ...

    async def find_one(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
    ) -> Optional[T]:
        ...

    async def find_many(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        sort: Optional[List[SortParam]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_deleted: bool = False,
    ) -> List[T]:
        ...

    async def exists(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        id: Optional[Union[uuid.UUID, str]] = None,
        include_deleted: bool = False,
    ) -> bool:
        ...

    async def count(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
    ) -> int:
        ...

    async def paginated_query(
        self,
        session: Any,
        params: OffsetParams,
        filters: Optional[List[FilterParam]] = None,
        sort: Optional[List[SortParam]] = None,
        include_deleted: bool = False,
    ) -> PageResult[T]:
        ...

    async def cursor_paginated_query(
        self,
        session: Any,
        params: CursorParams,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
    ) -> CursorResult[T]:
        ...

    async def create(
        self,
        session: Any,
        obj_in: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> T:
        ...

    async def create_many(
        self,
        session: Any,
        objs_in: List[Dict[str, Any]],
        actor_id: Optional[str] = None,
    ) -> List[T]:
        ...

    async def update(
        self,
        session: Any,
        entity_or_id: Union[T, uuid.UUID, str],
        obj_in: Dict[str, Any],
        expected_version: Optional[int] = None,
        actor_id: Optional[str] = None,
    ) -> T:
        ...

    async def update_many(
        self,
        session: Any,
        filters: List[FilterParam],
        obj_in: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> int:
        ...

    async def soft_delete(
        self,
        session: Any,
        entity_or_id: Union[T, uuid.UUID, str],
        actor_id: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> T:
        ...

    async def restore(
        self,
        session: Any,
        entity_or_id: Union[T, uuid.UUID, str],
        actor_id: Optional[str] = None,
    ) -> T:
        ...

    async def hard_delete(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
    ) -> bool:
        ...

    async def bulk_delete(
        self,
        session: Any,
        ids: Sequence[Union[uuid.UUID, str]],
        soft: bool = True,
        actor_id: Optional[str] = None,
    ) -> int:
        ...


@runtime_checkable
class ITenantRepository(IBaseRepository[T], Protocol):
    """Repository contract enforcing automatic multi-tenant organization scoping."""

    organization_id: uuid.UUID

    async def get_by_id_in_org(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
        organization_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[T]:
        ...

    async def count_by_org(
        self,
        session: Any,
        organization_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> int:
        ...


@runtime_checkable
class ISearchRepository(Protocol, Generic[T]):
    """Contract for full-text search and vector querying."""

    async def search(
        self,
        session: Any,
        search_query: str,
        filters: Optional[List[FilterParam]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[T], int]:
        ...


@runtime_checkable
class IAuditRepository(Protocol):
    """Contract for audit trail retrieval and reporting."""

    async def log_event(
        self,
        session: Any,
        event_type: str,
        actor_id: Optional[str],
        organization_id: Optional[uuid.UUID],
        resource_type: str,
        resource_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Any:
        ...
