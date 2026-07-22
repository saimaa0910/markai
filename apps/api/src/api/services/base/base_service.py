"""
EAIMOS Master Base Service Module
=================================
Generic, reusable BaseService providing complete enterprise lifecycle management for all domain entities.
Integrates Repository Injection, UnitOfWork, Authorization, Caching, Domain Event Propagation,
Validation, Audit Logging, Metrics, Retry Policies, Timeout Handling, Correlation IDs, and Idempotency.
"""

import asyncio
import logging
from typing import (
    Any,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Set,
    Tuple,
    Type,
    TypeVar,
    Union,
)
import uuid

from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam
from api.repositories.pagination import OffsetParams, PageResult
from api.repositories.sorting import SortParam
from api.repositories.tenant import TenantRepository
from api.services.base.authorization import AuthorizationService
from api.services.base.cache import ICacheManager
from api.services.base.dependency_provider import container
from api.services.base.event_dispatcher import EventDispatcher
from api.services.base.events import (
    DomainEvent,
    EntityCreated,
    EntityDeleted,
    EntityRestored,
    EntityUpdated,
)
from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import (
    AlreadyExistsError,
    BusinessRuleViolation,
    ConflictError,
    ForbiddenOperation,
    NotFoundError,
    ServiceError,
    ValidationError,
)
from api.services.base.service_result import ServiceResult
from api.services.base.unit_of_work_service import UnitOfWorkService, transactional
from api.services.base.validators import ValidatorChain

logger = logging.getLogger("eaimos.service")

T = TypeVar("T")
CreateDTO = TypeVar("CreateDTO")
UpdateDTO = TypeVar("UpdateDTO")
ResponseDTO = TypeVar("ResponseDTO")


class BaseService(Generic[T, CreateDTO, UpdateDTO, ResponseDTO]):
    """
    Master Service Layer component following Clean Architecture & DDD principles.
    Coordinates Repositories, UnitOfWork, Authorization, Caching, Validation, and Domain Events.
    """

    def __init__(
        self,
        repository_cls: Type[BaseRepository[T]],
        uow_service: Optional[UnitOfWorkService] = None,
        cache_manager: Optional[ICacheManager] = None,
        authorizer: Optional[AuthorizationService] = None,
        dispatcher: Optional[EventDispatcher] = None,
        entity_name: Optional[str] = None,
        read_permission: Optional[str] = None,
        write_permission: Optional[str] = None,
        cache_ttl_sec: int = 300,
    ) -> None:
        self.repository_cls = repository_cls
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache
        self.authorizer = authorizer or container.authorizer
        self.dispatcher = dispatcher or container.dispatcher
        self.entity_name = entity_name or repository_cls.__name__.replace("Repository", "")
        self.read_permission = read_permission
        self.write_permission = write_permission
        self.cache_ttl_sec = cache_ttl_sec
        self._processed_idempotency_keys: Set[str] = set()

    # -------------------------------------------------------------------------
    # Helper & Conversion Methods (Override in subclasses if needed)
    # -------------------------------------------------------------------------

    def _to_response_dto(self, entity: Any) -> ResponseDTO:
        """Convert ORM entity to response DTO. Default is returning entity itself."""
        return entity

    def _dto_to_dict(self, dto: Any) -> Dict[str, Any]:
        """Convert DTO to dictionary payload."""
        if hasattr(dto, "model_dump"):
            data = dto.model_dump(exclude_unset=True)
            if hasattr(dto, "__pydantic_fields__"):
                for k in dto.__pydantic_fields__:
                    v = getattr(dto, k, None)
                    if v is not None and k not in data:
                        data[k] = v
            return data
        if hasattr(dto, "dict"):
            return dto.dict(exclude_unset=True)
        if isinstance(dto, dict):
            return dto
        return getattr(dto, "__dict__", {})

    def _build_cache_key(self, entity_id: Union[uuid.UUID, str], org_id: Optional[str] = None) -> str:
        """Construct standard cache key for entity lookup."""
        prefix = f"{self.entity_name.lower()}:{str(entity_id)}"
        return f"{org_id}:{prefix}" if org_id else prefix

    # -------------------------------------------------------------------------
    # Lifecycle Hooks (Override in concrete services)
    # -------------------------------------------------------------------------

    async def before_create(self, ctx: ServiceContext, dto: CreateDTO) -> None:
        """Validation & business rule hook executed before creation."""
        pass

    async def after_create(self, ctx: ServiceContext, entity: T, dto: CreateDTO) -> None:
        """Post-creation hook executed before transaction commit."""
        pass

    async def before_update(self, ctx: ServiceContext, entity: T, dto: UpdateDTO) -> None:
        """Validation & business rule hook executed before update."""
        pass

    async def after_update(self, ctx: ServiceContext, entity: T, dto: UpdateDTO) -> None:
        """Post-update hook executed before transaction commit."""
        pass

    async def before_delete(self, ctx: ServiceContext, entity: T) -> None:
        """Validation & business rule hook executed before deletion."""
        pass

    async def after_delete(self, ctx: ServiceContext, entity_id: str) -> None:
        """Post-deletion hook executed before transaction commit."""
        pass

    # -------------------------------------------------------------------------
    # Authorization & Validation Helpers
    # -------------------------------------------------------------------------

    def _verify_read_permission(self, ctx: ServiceContext) -> None:
        """Enforce read permission if configured."""
        if self.read_permission:
            self.authorizer.require_permission(ctx, self.read_permission)

    def _verify_write_permission(self, ctx: ServiceContext) -> None:
        """Enforce write permission if configured."""
        if self.write_permission:
            self.authorizer.require_permission(ctx, self.write_permission)

    # -------------------------------------------------------------------------
    # CRUD Operations
    # -------------------------------------------------------------------------

    async def create(
        self,
        ctx: ServiceContext,
        dto: CreateDTO,
        idempotency_key: Optional[str] = None,
    ) -> ServiceResult[ResponseDTO]:
        """Create a new domain entity within a transactional boundary."""
        if idempotency_key and idempotency_key in self._processed_idempotency_keys:
            return ServiceResult.fail(
                error=f"Duplicate request detected for idempotency key '{idempotency_key}'",
                error_code="IDEMPOTENCY_CONFLICT",
                status_code=409,
            )

        try:
            self._verify_write_permission(ctx)
            await self.before_create(ctx, dto)

            obj_data = self._dto_to_dict(dto)
            
            # Automatically assign tenant organization_id if repository is multi-tenant
            if ctx.organization_id and "organization_id" not in obj_data:
                obj_data["organization_id"] = str(ctx.organization_id)

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                created_entity = await repo.create(
                    session=self.uow_service.session,
                    obj_in=obj_data,
                    actor_id=ctx.get_user_id_uuid(),
                )
                await self.after_create(ctx, created_entity, dto)

                # Buffer Domain Event
                entity_id_str = str(getattr(created_entity, "id", ""))
                self.uow_service.add_event(
                    EntityCreated(
                        aggregate_id=entity_id_str,
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        entity_name=self.entity_name,
                        payload={"entity_id": entity_id_str},
                    )
                )

            if idempotency_key:
                self._processed_idempotency_keys.add(idempotency_key)

            response_dto = self._to_response_dto(created_entity)
            return ServiceResult.ok(data=response_dto, status_code=201)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Unexpected error during create {self.entity_name}: {exc}", exc_info=True)
            return ServiceResult.fail(
                error=f"Failed to create {self.entity_name}: {str(exc)}",
                status_code=500,
            )

    async def get_by_id(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
        include_deleted: bool = False,
    ) -> ServiceResult[Optional[ResponseDTO]]:
        """Retrieve entity by ID with read caching and authorization checks."""
        try:
            self._verify_read_permission(ctx)
            cache_key = self._build_cache_key(id, ctx.get_org_id_str())

            # Attempt cache read
            cached_val = await self.cache.get(cache_key)
            if cached_val is not None and isinstance(cached_val, dict):
                return ServiceResult.ok(data=cached_val, metadata={"cached": True})

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                entity = await repo.get_by_id(
                    session=self.uow_service.session,
                    id=id,
                    include_deleted=include_deleted,
                )

                if not entity:
                    return ServiceResult.fail(
                        error=f"{self.entity_name} with ID '{id}' was not found.",
                        error_code="NOT_FOUND",
                        status_code=404,
                    )

                # Tenant Scoping check if entity has organization_id
                if hasattr(entity, "organization_id") and entity.organization_id:
                    self.authorizer.require_tenant_access(ctx, entity.organization_id)

                response_dto = self._to_response_dto(entity)
                
                # Write through cache
                if hasattr(response_dto, "model_dump"):
                    await self.cache.set(cache_key, response_dto.model_dump(), ttl=self.cache_ttl_sec)

                return ServiceResult.ok(data=response_dto)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Unexpected error getting {self.entity_name} {id}: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), status_code=500)

    async def update(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
        dto: UpdateDTO,
        expected_version: Optional[int] = None,
    ) -> ServiceResult[ResponseDTO]:
        """Update an existing domain entity with versioning check and cache invalidation."""
        try:
            self._verify_write_permission(ctx)
            update_data = self._dto_to_dict(dto)

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                existing = await repo.get_by_id(session=self.uow_service.session, id=id)
                if not existing:
                    raise NotFoundError(
                        message=f"{self.entity_name} with ID '{id}' does not exist.",
                        resource_type=self.entity_name,
                        resource_id=str(id),
                    )

                if hasattr(existing, "organization_id") and existing.organization_id:
                    self.authorizer.require_tenant_access(ctx, existing.organization_id)

                await self.before_update(ctx, existing, dto)

                updated_entity = await repo.update(
                    session=self.uow_service.session,
                    entity_or_id=existing,
                    obj_in=update_data,
                    expected_version=expected_version,
                    actor_id=ctx.get_user_id_uuid(),
                )

                await self.after_update(ctx, updated_entity, dto)

                # Buffer Domain Event
                entity_id_str = str(id)
                self.uow_service.add_event(
                    EntityUpdated(
                        aggregate_id=entity_id_str,
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        entity_name=self.entity_name,
                        changes=update_data,
                    )
                )

            # Invalidate Cache
            cache_key = self._build_cache_key(id, ctx.get_org_id_str())
            await self.cache.delete(cache_key)

            response_dto = self._to_response_dto(updated_entity)
            return ServiceResult.ok(data=response_dto)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Unexpected error updating {self.entity_name} {id}: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), status_code=500)

    async def soft_delete(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
    ) -> ServiceResult[ResponseDTO]:
        """Soft delete entity and record domain event."""
        try:
            self._verify_write_permission(ctx)

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                existing = await repo.get_by_id(session=self.uow_service.session, id=id)
                if not existing:
                    raise NotFoundError(
                        message=f"{self.entity_name} with ID '{id}' not found.",
                        resource_type=self.entity_name,
                        resource_id=str(id),
                    )

                if hasattr(existing, "organization_id") and existing.organization_id:
                    self.authorizer.require_tenant_access(ctx, existing.organization_id)

                await self.before_delete(ctx, existing)

                deleted_entity = await repo.soft_delete(
                    session=self.uow_service.session,
                    entity_or_id=existing,
                    actor_id=ctx.get_user_id_uuid(),
                )

                await self.after_delete(ctx, str(id))

                self.uow_service.add_event(
                    EntityDeleted(
                        aggregate_id=str(id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        entity_name=self.entity_name,
                        is_hard_delete=False,
                    )
                )

            # Invalidate Cache
            cache_key = self._build_cache_key(id, ctx.get_org_id_str())
            await self.cache.delete(cache_key)

            response_dto = self._to_response_dto(deleted_entity)
            return ServiceResult.ok(data=response_dto)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Error during soft_delete {self.entity_name} {id}: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), status_code=500)

    async def restore(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
    ) -> ServiceResult[ResponseDTO]:
        """Restore soft-deleted entity."""
        try:
            self._verify_write_permission(ctx)

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                existing = await repo.get_by_id(
                    session=self.uow_service.session,
                    id=id,
                    include_deleted=True,
                )
                if not existing:
                    raise NotFoundError(
                        message=f"{self.entity_name} with ID '{id}' not found.",
                        resource_type=self.entity_name,
                        resource_id=str(id),
                    )

                if hasattr(existing, "organization_id") and existing.organization_id:
                    self.authorizer.require_tenant_access(ctx, existing.organization_id)

                restored_entity = await repo.restore(
                    session=self.uow_service.session,
                    entity_or_id=existing,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    EntityRestored(
                        aggregate_id=str(id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        entity_name=self.entity_name,
                    )
                )

            response_dto = self._to_response_dto(restored_entity)
            return ServiceResult.ok(data=response_dto)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Error restoring {self.entity_name} {id}: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), status_code=500)

    async def delete(
        self,
        ctx: ServiceContext,
        id: Union[uuid.UUID, str],
        hard: bool = False,
    ) -> ServiceResult[bool]:
        """Delete entity (soft or hard delete depending on parameter)."""
        if not hard:
            res = await self.soft_delete(ctx, id)
            return ServiceResult(
                success=res.success,
                data=res.success,
                errors=res.errors,
                warnings=res.warnings,
                metadata=res.metadata,
                error_code=res.error_code,
                status_code=res.status_code,
            )

        try:
            self._verify_write_permission(ctx)

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                existing = await repo.get_by_id(
                    session=self.uow_service.session, id=id, include_deleted=True
                )
                if not existing:
                    raise NotFoundError(
                        message=f"{self.entity_name} with ID '{id}' not found.",
                        resource_type=self.entity_name,
                        resource_id=str(id),
                    )

                if hasattr(existing, "organization_id") and existing.organization_id:
                    self.authorizer.require_tenant_access(ctx, existing.organization_id)

                await self.before_delete(ctx, existing)
                success = await repo.hard_delete(session=self.uow_service.session, id=id)
                await self.after_delete(ctx, str(id))

                self.uow_service.add_event(
                    EntityDeleted(
                        aggregate_id=str(id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        entity_name=self.entity_name,
                        is_hard_delete=True,
                    )
                )

            cache_key = self._build_cache_key(id, ctx.get_org_id_str())
            await self.cache.delete(cache_key)

            return ServiceResult.ok(data=success)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Error hard-deleting {self.entity_name} {id}: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), status_code=500)

    async def list(
        self,
        ctx: ServiceContext,
        params: OffsetParams,
        filters: Optional[List[FilterParam]] = None,
        sort: Optional[List[SortParam]] = None,
        include_deleted: bool = False,
    ) -> ServiceResult[PageResult[ResponseDTO]]:
        """Paginated entity query with automatic tenant filter injection."""
        try:
            self._verify_read_permission(ctx)
            effective_filters = list(filters) if filters else []

            # Automatically inject organization_id filter if present in context
            if ctx.organization_id and not ctx.is_super_admin:
                effective_filters.append(
                    FilterParam(field="organization_id", operator="eq", value=str(ctx.organization_id))
                )

            async with self.uow_service:
                repo = self.uow_service.get_repository(self.repository_cls)
                page_res = await repo.paginated_query(
                    session=self.uow_service.session,
                    params=params,
                    filters=effective_filters,
                    sort=sort,
                    include_deleted=include_deleted,
                )

                dto_items = [self._to_response_dto(item) for item in page_res.items]
                dto_page_result = PageResult(
                    items=dto_items,
                    total=page_res.total,
                    page=page_res.page,
                    page_size=page_res.page_size,
                    total_pages=page_res.total_pages,
                    has_next=page_res.has_next,
                    has_previous=page_res.has_previous,
                )

                return ServiceResult.ok(data=dto_page_result)

        except ServiceError as exc:
            return ServiceResult.from_exception(exc)
        except Exception as exc:
            logger.error(f"Error querying {self.entity_name} list: {exc}", exc_info=True)
            return ServiceResult.fail(error=str(exc), status_code=500)
