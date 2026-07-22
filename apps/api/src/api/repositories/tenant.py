"""
EAIMOS Multi-Tenant Base Repository
====================================
Repository base class enforcing strict tenant boundaries (organization_id).
Prevents cross-tenant data leaks at the ORM layer.
"""

from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Type,
    TypeVar,
    Union,
)
import uuid

from api.database.base import Base
from api.repositories.base import BaseRepository
from api.repositories.exceptions import TenantViolationError
from api.repositories.filters import FilterParam, FilterOperator
from api.repositories.interfaces import ITenantRepository
from api.repositories.pagination import (
    CursorParams,
    CursorResult,
    OffsetParams,
    PageResult,
)
from api.repositories.query_builder import QueryOptions
from api.repositories.sorting import SortParam

ModelType = TypeVar("ModelType", bound=Base)


class TenantRepository(BaseRepository[ModelType], ITenantRepository[ModelType]):
    """
    Tenant-enforcing repository.
    Guarantees that all operations are scoped to a given organization_id.
    """

    def __init__(self, model: Type[ModelType], organization_id: uuid.UUID) -> None:
        super().__init__(model)
        self.organization_id = organization_id

    def _inject_tenant_filter(
        self, filters: Optional[List[FilterParam]], target_org_id: Optional[uuid.UUID] = None
    ) -> List[FilterParam]:
        org_id = target_org_id or self.organization_id
        org_filter = FilterParam(field="organization_id", operator=FilterOperator.EQ, value=org_id)
        if filters is None:
            return [org_filter]

        # Ensure no existing organization_id filter contradicts current org context
        cleaned = [f for f in filters if f.field != "organization_id"]
        cleaned.append(org_filter)
        return cleaned

    def _validate_tenant_ownership(self, entity: ModelType) -> None:
        """Validate that an existing entity belongs to the configured organization context."""
        if hasattr(entity, "organization_id"):
            entity_org_id = getattr(entity, "organization_id")
            if entity_org_id != self.organization_id:
                raise TenantViolationError(
                    entity_name=self.model.__name__,
                    attempted_org_id=entity_org_id,
                    context_org_id=self.organization_id,
                )

    # ── Tenant-Scoped Read Operations ─────────────────────────────────────────
    async def get_by_id(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> Optional[ModelType]:
        filters = self._inject_tenant_filter([
            FilterParam(field="id", operator=FilterOperator.EQ, value=id)
        ])
        return await super().find_one(
            session=session,
            filters=filters,
            include_deleted=include_deleted,
            options=options,
        )

    async def get_by_id_in_org(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
        organization_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> Optional[ModelType]:
        filters = self._inject_tenant_filter(
            [FilterParam(field="id", operator=FilterOperator.EQ, value=id)],
            target_org_id=organization_id,
        )
        return await super().find_one(
            session=session,
            filters=filters,
            include_deleted=include_deleted,
        )

    async def get_by_ids(
        self,
        session: Any,
        ids: Sequence[Union[uuid.UUID, str]],
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> List[ModelType]:
        if not ids:
            return []
        filters = self._inject_tenant_filter([
            FilterParam(field="id", operator=FilterOperator.IN, value=list(ids))
        ])
        return await super().find_many(
            session=session,
            filters=filters,
            include_deleted=include_deleted,
            options=options,
        )

    async def find_one(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> Optional[ModelType]:
        tenant_filters = self._inject_tenant_filter(filters)
        return await super().find_one(
            session=session,
            filters=tenant_filters,
            include_deleted=include_deleted,
            options=options,
        )

    async def find_many(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        sort: Optional[List[SortParam]] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> List[ModelType]:
        tenant_filters = self._inject_tenant_filter(filters)
        return await super().find_many(
            session=session,
            filters=tenant_filters,
            sort=sort,
            limit=limit,
            offset=offset,
            include_deleted=include_deleted,
            options=options,
        )

    async def exists(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        id: Optional[Union[uuid.UUID, str]] = None,
        include_deleted: bool = False,
    ) -> bool:
        tenant_filters = self._inject_tenant_filter(filters)
        return await super().exists(
            session=session,
            filters=tenant_filters,
            id=id,
            include_deleted=include_deleted,
        )

    async def count(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
    ) -> int:
        tenant_filters = self._inject_tenant_filter(filters)
        return await super().count(
            session=session,
            filters=tenant_filters,
            include_deleted=include_deleted,
        )

    async def count_by_org(
        self,
        session: Any,
        organization_id: uuid.UUID,
        include_deleted: bool = False,
    ) -> int:
        filters = [FilterParam(field="organization_id", operator=FilterOperator.EQ, value=organization_id)]
        return await super().count(session=session, filters=filters, include_deleted=include_deleted)

    # ── Tenant-Scoped Write Operations ────────────────────────────────────────
    async def create(
        self,
        session: Any,
        obj_in: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> ModelType:
        data = dict(obj_in)
        data["organization_id"] = self.organization_id
        return await super().create(session=session, obj_in=data, actor_id=actor_id)

    async def create_many(
        self,
        session: Any,
        objs_in: List[Dict[str, Any]],
        actor_id: Optional[str] = None,
    ) -> List[ModelType]:
        prepared = []
        for obj in objs_in:
            d = dict(obj)
            d["organization_id"] = self.organization_id
            prepared.append(d)
        return await super().create_many(session=session, objs_in=prepared, actor_id=actor_id)

    async def update(
        self,
        session: Any,
        entity_or_id: Union[ModelType, uuid.UUID, str],
        obj_in: Dict[str, Any],
        expected_version: Optional[int] = None,
        actor_id: Optional[str] = None,
    ) -> ModelType:
        if isinstance(entity_or_id, self.model):
            self._validate_tenant_ownership(entity_or_id)
        else:
            existing = await self.get_by_id(session, entity_or_id)
            if not existing:
                raise TenantViolationError(
                    entity_name=self.model.__name__,
                    attempted_org_id=entity_or_id,
                    context_org_id=self.organization_id,
                )

        return await super().update(
            session=session,
            entity_or_id=entity_or_id,
            obj_in=obj_in,
            expected_version=expected_version,
            actor_id=actor_id,
        )

    async def soft_delete(
        self,
        session: Any,
        entity_or_id: Union[ModelType, uuid.UUID, str],
        actor_id: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> ModelType:
        if isinstance(entity_or_id, self.model):
            self._validate_tenant_ownership(entity_or_id)
        else:
            existing = await self.get_by_id(session, entity_or_id)
            if not existing:
                raise TenantViolationError(
                    entity_name=self.model.__name__,
                    attempted_org_id=entity_or_id,
                    context_org_id=self.organization_id,
                )

        return await super().soft_delete(
            session=session,
            entity_or_id=entity_or_id,
            actor_id=actor_id,
            expected_version=expected_version,
        )
