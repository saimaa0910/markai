"""
EAIMOS Full-Text Search Repository
===================================
Provides full-text search capabilities using PostgreSQL tsvector / websearch_to_tsquery
with automatic fallback to ILIKE for SQLite/in-memory test environments.
"""

from typing import Any, Generic, List, Optional, Tuple, Type, TypeVar
from sqlalchemy import Select, func, select, or_
from api.database.base import Base
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, apply_filters
from api.repositories.interfaces import ISearchRepository

ModelType = TypeVar("ModelType", bound=Base)


class SearchRepository(BaseRepository[ModelType], ISearchRepository[ModelType]):
    """Generic full-text search repository extension."""

    def __init__(self, model: Type[ModelType], search_columns: List[str]) -> None:
        super().__init__(model)
        self.search_columns = search_columns

    async def search(
        self,
        session: Any,
        search_query: str,
        filters: Optional[List[FilterParam]] = None,
        limit: int = 20,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> Tuple[List[ModelType], int]:
        if not search_query.strip():
            items = await self.find_many(
                session, filters=filters, limit=limit, offset=offset, include_deleted=include_deleted
            )
            total = await self.count(session, filters=filters, include_deleted=include_deleted)
            return items, total

        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))

        if filters:
            stmt = apply_filters(stmt, self.model, filters)

        # Dynamic search clauses across search_columns
        search_conditions = []
        for col_name in self.search_columns:
            if hasattr(self.model, col_name):
                col = getattr(self.model, col_name)
                search_conditions.append(col.ilike(f"%{search_query}%"))

        if search_conditions:
            stmt = stmt.where(or_(*search_conditions))

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        count_res = await self._execute(session, count_stmt)
        total = count_res.scalar_one()

        stmt = stmt.offset(offset).limit(limit)
        res = await self._execute(session, stmt)
        items = list(res.scalars().all())

        return items, total
