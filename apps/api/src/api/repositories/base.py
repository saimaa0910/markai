"""
EAIMOS Generic Base Repository
==============================
Production-grade generic base repository for SQLAlchemy 2.x models.
Supports:
- Dual Async/Sync SQLAlchemy 2.0 session execution
- CRUD & Bulk Operations
- Soft Deletion & Restoration
- Optimistic Locking (version tracking)
- Dynamic Filtering, Sorting & Pagination (Offset & Keyset Cursor)
- Metric hooks for query telemetry
- Domain exception mapping
"""

import datetime
import inspect
import time
from typing import (
    Any,
    Callable,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    TypeVar,
    Union,
)
import uuid

from sqlalchemy import (
    Select,
    and_,
    delete,
    func,
    insert,
    or_,
    select,
    update as sql_update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.base import Base
from api.repositories.exceptions import (
    DatabaseConstraintError,
    DuplicateEntityError,
    EntityNotFoundError,
    OptimisticLockError,
    RepositoryError,
)
from api.repositories.filters import FilterParam, apply_filters
from api.repositories.interfaces import IBaseRepository
from api.repositories.pagination import (
    CursorParams,
    CursorResult,
    OffsetParams,
    PageResult,
)
from api.repositories.query_builder import QueryOptions
from api.repositories.sorting import SortParam, apply_sorting

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType], IBaseRepository[ModelType]):
    """
    Generic SQLAlchemy 2.x Repository implementation.
    Encapsulates all direct database interaction logic.
    """

    def __init__(self, model: Type[ModelType]) -> None:
        self.model = model
        self.metrics_hook: Optional[Callable[[str, float, bool], None]] = None

    # ── Internal Execution Helpers (Supports AsyncSession & Session) ─────────
    async def _execute(self, session: Any, stmt: Any) -> Any:
        start_time = time.monotonic()
        success = True
        try:
            res = session.execute(stmt)
            if inspect.isawaitable(res):
                res = await res
            return res
        except IntegrityError as exc:
            success = False
            self._handle_integrity_error(exc)
        except Exception as exc:
            success = False
            if isinstance(exc, RepositoryError):
                raise exc
            raise RepositoryError(f"Database query failed: {exc}") from exc
        finally:
            duration = time.monotonic() - start_time
            if self.metrics_hook:
                self.metrics_hook(self.model.__name__, duration, success)

    async def _flush(self, session: Any) -> None:
        res = session.flush()
        if inspect.isawaitable(res):
            await res

    def _handle_integrity_error(self, exc: IntegrityError) -> None:
        orig = str(exc.orig) if exc.orig else str(exc)
        if "unique constraint" in orig.lower() or "duplicate key" in orig.lower():
            raise DuplicateEntityError(
                entity_name=self.model.__name__,
                conflict_field="constraint",
                conflict_value=orig,
            ) from exc
        raise DatabaseConstraintError(
            constraint_name="integrity_constraint",
            original_error=orig,
        ) from exc

    # ── Read Operations ───────────────────────────────────────────────────────
    async def get_by_id(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> Optional[ModelType]:
        stmt = select(self.model).where(self.model.id == id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if options:
            stmt = options.apply(stmt)

        res = await self._execute(session, stmt)
        return res.scalar_one_or_none()

    async def get_by_ids(
        self,
        session: Any,
        ids: Sequence[Union[uuid.UUID, str]],
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> List[ModelType]:
        if not ids:
            return []
        stmt = select(self.model).where(self.model.id.in_(ids))
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if options:
            stmt = options.apply(stmt)

        res = await self._execute(session, stmt)
        return list(res.scalars().all())

    async def find_one(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> Optional[ModelType]:
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            stmt = apply_filters(stmt, self.model, filters)
        if options:
            stmt = options.apply(stmt)

        res = await self._execute(session, stmt)
        return res.scalar_one_or_none()

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
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            stmt = apply_filters(stmt, self.model, filters)
        if sort:
            stmt = apply_sorting(stmt, self.model, sort)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)
        if options:
            stmt = options.apply(stmt)

        res = await self._execute(session, stmt)
        return list(res.scalars().all())

    async def exists(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        id: Optional[Union[uuid.UUID, str]] = None,
        include_deleted: bool = False,
    ) -> bool:
        stmt = select(func.count(self.model.id))
        if id is not None:
            stmt = stmt.where(self.model.id == id)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            stmt = apply_filters(stmt, self.model, filters)

        res = await self._execute(session, stmt)
        count = res.scalar_one()
        return count > 0

    async def count(
        self,
        session: Any,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
    ) -> int:
        stmt = select(func.count(self.model.id))
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            stmt = apply_filters(stmt, self.model, filters)

        res = await self._execute(session, stmt)
        return res.scalar_one()

    # ── Pagination ────────────────────────────────────────────────────────────
    async def paginated_query(
        self,
        session: Any,
        params: OffsetParams,
        filters: Optional[List[FilterParam]] = None,
        sort: Optional[List[SortParam]] = None,
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> PageResult[ModelType]:
        total = await self.count(session, filters=filters, include_deleted=include_deleted)
        items = await self.find_many(
            session=session,
            filters=filters,
            sort=sort,
            limit=params.limit,
            offset=params.offset,
            include_deleted=include_deleted,
            options=options,
        )
        return PageResult.create(items=items, total=total, params=params)

    async def cursor_paginated_query(
        self,
        session: Any,
        params: CursorParams,
        filters: Optional[List[FilterParam]] = None,
        include_deleted: bool = False,
        options: Optional[QueryOptions] = None,
    ) -> CursorResult[ModelType]:
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        if filters:
            stmt = apply_filters(stmt, self.model, filters)

        sort_col = getattr(self.model, params.sort_field, getattr(self.model, "created_at"))
        if params.cursor:
            decoded = CursorResult.decode_cursor(params.cursor)
            cursor_val = decoded.get(params.sort_field)
            cursor_id = decoded.get("id")
            if cursor_val is not None and cursor_id is not None:
                if params.sort_order.lower() == "desc":
                    stmt = stmt.where(
                        or_(
                            sort_col < cursor_val,
                            and_(sort_col == cursor_val, self.model.id < uuid.UUID(str(cursor_id))),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            sort_col > cursor_val,
                            and_(sort_col == cursor_val, self.model.id > uuid.UUID(str(cursor_id))),
                        )
                    )

        if params.sort_order.lower() == "desc":
            stmt = stmt.order_by(sort_col.desc(), self.model.id.desc())
        else:
            stmt = stmt.order_by(sort_col.asc(), self.model.id.asc())

        stmt = stmt.limit(params.limit + 1)
        if options:
            stmt = options.apply(stmt)

        res = await self._execute(session, stmt)
        records = list(res.scalars().all())

        has_more = len(records) > params.limit
        items = records[: params.limit]

        next_cursor = None
        if has_more and items:
            last_item = items[-1]
            next_val = getattr(last_item, params.sort_field, getattr(last_item, "created_at", None))
            next_cursor = CursorResult.encode_cursor({
                params.sort_field: str(next_val),
                "id": str(last_item.id),
            })

        return CursorResult(
            items=items,
            next_cursor=next_cursor,
            has_more=has_more,
        )

    def _resolve_actor_val(self, attr_name: str, actor_id: Any) -> Any:
        """Resolve actor_id as UUID or str based on model column type."""
        if not actor_id:
            return None
        actor_str = str(actor_id)
        try:
            col_attr = getattr(self.model, attr_name, None)
            if col_attr and hasattr(col_attr, "property") and hasattr(col_attr.property, "columns"):
                type_name = col_attr.property.columns[0].type.__class__.__name__
                if "UUID" in type_name:
                    return actor_id if isinstance(actor_id, uuid.UUID) else uuid.UUID(actor_str)
        except Exception:
            pass
        return actor_str

    # ── Write Operations ──────────────────────────────────────────────────────
    async def create(
        self,
        session: Any,
        obj_in: Dict[str, Any],
        actor_id: Optional[Any] = None,
    ) -> ModelType:
        data = dict(obj_in)
        if actor_id:
            if hasattr(self.model, "created_by"):
                data["created_by"] = self._resolve_actor_val("created_by", actor_id)
            if hasattr(self.model, "updated_by"):
                data["updated_by"] = self._resolve_actor_val("updated_by", actor_id)

        instance = self.model(**data)
        session.add(instance)
        await self._flush(session)
        return instance

    async def create_many(
        self,
        session: Any,
        objs_in: List[Dict[str, Any]],
        actor_id: Optional[Any] = None,
    ) -> List[ModelType]:
        instances = []
        for obj in objs_in:
            data = dict(obj)
            if actor_id:
                if hasattr(self.model, "created_by"):
                    data["created_by"] = self._resolve_actor_val("created_by", actor_id)
                if hasattr(self.model, "updated_by"):
                    data["updated_by"] = self._resolve_actor_val("updated_by", actor_id)
            inst = self.model(**data)
            instances.append(inst)
            session.add(inst)
        await self._flush(session)
        return instances

    async def update(
        self,
        session: Any,
        entity_or_id: Union[ModelType, uuid.UUID, str],
        obj_in: Dict[str, Any],
        expected_version: Optional[int] = None,
        actor_id: Optional[Any] = None,
    ) -> ModelType:
        if isinstance(entity_or_id, self.model):
            entity = entity_or_id
        else:
            entity = await self.get_by_id(session, entity_or_id)
            if not entity:
                raise EntityNotFoundError(self.model.__name__, entity_or_id)

        # Optimistic Locking Check
        if expected_version is not None and hasattr(entity, "version"):
            if entity.version != expected_version:
                raise OptimisticLockError(
                    entity_name=self.model.__name__,
                    identifier=entity.id,
                    expected_version=expected_version,
                    actual_version=entity.version,
                )

        for field, value in obj_in.items():
            if hasattr(entity, field) and field not in ("id", "created_at", "created_by"):
                setattr(entity, field, value)

        if actor_id and hasattr(entity, "updated_by"):
            entity.updated_by = self._resolve_actor_val("updated_by", actor_id)

        if hasattr(entity, "version"):
            entity.version += 1

        if hasattr(entity, "updated_at"):
            entity.updated_at = datetime.datetime.now(datetime.timezone.utc)

        await self._flush(session)
        return entity

    async def update_many(
        self,
        session: Any,
        filters: List[FilterParam],
        obj_in: Dict[str, Any],
        actor_id: Optional[str] = None,
    ) -> int:
        data = dict(obj_in)
        if actor_id and hasattr(self.model, "updated_by"):
            data["updated_by"] = actor_id
        if hasattr(self.model, "updated_at"):
            data["updated_at"] = datetime.datetime.now(datetime.timezone.utc)

        stmt = sql_update(self.model)
        stmt = apply_filters(stmt, self.model, filters)
        stmt = stmt.values(**data)

        res = await self._execute(session, stmt)
        return res.rowcount

    # ── Delete & Restore ─────────────────────────────────────────────────────
    async def soft_delete(
        self,
        session: Any,
        entity_or_id: Union[ModelType, uuid.UUID, str],
        actor_id: Optional[str] = None,
        expected_version: Optional[int] = None,
    ) -> ModelType:
        if isinstance(entity_or_id, self.model):
            entity = entity_or_id
        else:
            entity = await self.get_by_id(session, entity_or_id)
            if not entity:
                raise EntityNotFoundError(self.model.__name__, entity_or_id)

        if expected_version is not None and hasattr(entity, "version"):
            if entity.version != expected_version:
                raise OptimisticLockError(
                    entity_name=self.model.__name__,
                    identifier=entity.id,
                    expected_version=expected_version,
                    actual_version=entity.version,
                )

        if hasattr(entity, "deleted_at"):
            entity.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        if actor_id and hasattr(entity, "updated_by"):
            entity.updated_by = actor_id

        await self._flush(session)
        return entity

    async def restore(
        self,
        session: Any,
        entity_or_id: Union[ModelType, uuid.UUID, str],
        actor_id: Optional[str] = None,
    ) -> ModelType:
        if isinstance(entity_or_id, self.model):
            entity = entity_or_id
        else:
            entity = await self.get_by_id(session, entity_or_id, include_deleted=True)
            if not entity:
                raise EntityNotFoundError(self.model.__name__, entity_or_id)

        if hasattr(entity, "deleted_at"):
            entity.deleted_at = None
        if actor_id and hasattr(entity, "updated_by"):
            entity.updated_by = actor_id

        await self._flush(session)
        return entity

    async def hard_delete(
        self,
        session: Any,
        id: Union[uuid.UUID, str],
    ) -> bool:
        stmt = delete(self.model).where(self.model.id == id)
        res = await self._execute(session, stmt)
        return res.rowcount > 0

    async def bulk_delete(
        self,
        session: Any,
        ids: Sequence[Union[uuid.UUID, str]],
        soft: bool = True,
        actor_id: Optional[str] = None,
    ) -> int:
        if not ids:
            return 0
        if soft and hasattr(self.model, "deleted_at"):
            values: Dict[str, Any] = {"deleted_at": datetime.datetime.now(datetime.timezone.utc)}
            if actor_id and hasattr(self.model, "updated_by"):
                values["updated_by"] = actor_id
            stmt = sql_update(self.model).where(self.model.id.in_(ids)).values(**values)
        else:
            stmt = delete(self.model).where(self.model.id.in_(ids))

        res = await self._execute(session, stmt)
        return res.rowcount

    # ── Bulk Operations ───────────────────────────────────────────────────────
    async def bulk_insert(
        self,
        session: Any,
        objs_in: List[Dict[str, Any]],
        actor_id: Optional[str] = None,
    ) -> int:
        if not objs_in:
            return 0
        prepared = []
        for item in objs_in:
            d = dict(item)
            if "id" not in d:
                d["id"] = uuid.uuid4()
            if actor_id:
                if hasattr(self.model, "created_by"):
                    d["created_by"] = actor_id
                if hasattr(self.model, "updated_by"):
                    d["updated_by"] = actor_id
            prepared.append(d)

        stmt = insert(self.model).values(prepared)
        res = await self._execute(session, stmt)
        return res.rowcount or len(prepared)

    async def bulk_update(
        self,
        session: Any,
        updates: List[Dict[str, Any]],
    ) -> int:
        if not updates:
            return 0
        count = 0
        for item in updates:
            item_id = item.get("id")
            if not item_id:
                continue
            payload = {k: v for k, v in item.items() if k != "id"}
            stmt = sql_update(self.model).where(self.model.id == item_id).values(**payload)
            res = await self._execute(session, stmt)
            count += res.rowcount
        return count

    async def bulk_upsert(
        self,
        session: Any,
        records: List[Dict[str, Any]],
        index_elements: List[str],
    ) -> int:
        """Upsert records (inserts or updates on index element collision)."""
        if not records:
            return 0
        count = 0
        for rec in records:
            # Check existence by index elements
            filters = [FilterParam(field=k, operator="eq", value=rec[k]) for k in index_elements if k in rec]
            existing = await self.find_one(session, filters=filters, include_deleted=True)
            if existing:
                await self.update(session, existing, rec)
            else:
                await self.create(session, rec)
            count += 1
        return count
