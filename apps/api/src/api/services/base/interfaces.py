"""
EAIMOS Service Layer Interfaces & Protocols
============================================
Establishes clear abstract protocols for BaseService, ServiceContext, Cache, Authorization,
Event Dispatchers, and Validators across all EAIMOS modules.
"""

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Protocol,
    Sequence,
    TypeVar,
    Union,
    runtime_checkable,
)
import uuid

from api.repositories.filters import FilterParam
from api.repositories.pagination import OffsetParams, PageResult
from api.repositories.sorting import SortParam
from api.services.base.events import DomainEvent
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult

T = TypeVar("T")
CreateDTO = TypeVar("CreateDTO")
UpdateDTO = TypeVar("UpdateDTO")
ResponseDTO = TypeVar("ResponseDTO")


@runtime_checkable
class IAuthorizer(Protocol):
    """Protocol for Authorization engines."""

    def check_permission(self, ctx: ServiceContext, permission: str) -> bool:
        ...

    def require_permission(self, ctx: ServiceContext, permission: str) -> None:
        ...

    def check_role(self, ctx: ServiceContext, role: str) -> bool:
        ...

    def require_role(self, ctx: ServiceContext, role: str) -> None:
        ...

    def check_tenant_access(self, ctx: ServiceContext, target_org_id: Union[uuid.UUID, str]) -> bool:
        ...

    def require_tenant_access(self, ctx: ServiceContext, target_org_id: Union[uuid.UUID, str]) -> None:
        ...

    def check_ownership(
        self,
        ctx: ServiceContext,
        resource_owner_id: Optional[Union[uuid.UUID, str]],
        allow_admin_override: bool = True,
    ) -> bool:
        ...


@runtime_checkable
class IEventDispatcherProtocol(Protocol):
    """Protocol for Domain Event dispatchers."""

    async def publish(self, event: DomainEvent) -> None:
        ...

    async def publish_many(self, events: Sequence[DomainEvent]) -> None:
        ...


@runtime_checkable
class IBaseService(Protocol, Generic[T, CreateDTO, UpdateDTO, ResponseDTO]):
    """Generic contract for all EAIMOS enterprise services."""

    async def create(
        self,
        ctx: ServiceContext,
        dto: CreateDTO,
    ) -> ServiceResult[ResponseDTO]:
        ...

    async def update(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
        dto: UpdateDTO,
        expected_version: Optional[int] = None,
    ) -> ServiceResult[ResponseDTO]:
        ...

    async def delete(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
        hard: bool = False,
    ) -> ServiceResult[bool]:
        ...

    async def soft_delete(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
    ) -> ServiceResult[ResponseDTO]:
        ...

    async def restore(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
    ) -> ServiceResult[ResponseDTO]:
        ...

    async def get_by_id(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
        include_deleted: bool = False,
    ) -> ServiceResult[Optional[ResponseDTO]]:
        ...

    async def list(
        self,
        ctx: ServiceContext,
        params: OffsetParams,
        filters: Optional[List[FilterParam]] = None,
        sort: Optional[List[SortParam]] = None,
        include_deleted: bool = False,
    ) -> ServiceResult[PageResult[ResponseDTO]]:
        ...
