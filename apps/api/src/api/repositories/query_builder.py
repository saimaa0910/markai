"""
EAIMOS Query Builder & Eager Loading Strategy
==============================================
Prevents N+1 query problems and optimizes data retrieval with SQLAlchemy 2.0 options.
"""

from typing import Any, List, Optional, Type
from sqlalchemy import Select
from sqlalchemy.orm import (
    contains_eager,
    defer,
    joinedload,
    load_only,
    selectinload,
    undefer,
)


class QueryOptions:
    """Encapsulates ORM eager loading, column deferrals, and projection options."""

    def __init__(
        self,
        selectin_relationships: Optional[List[Any]] = None,
        joined_relationships: Optional[List[Any]] = None,
        contains_eager_relationships: Optional[List[Any]] = None,
        load_only_fields: Optional[List[Any]] = None,
        defer_fields: Optional[List[Any]] = None,
    ) -> None:
        self.selectin_relationships = selectin_relationships or []
        self.joined_relationships = joined_relationships or []
        self.contains_eager_relationships = contains_eager_relationships or []
        self.load_only_fields = load_only_fields or []
        self.defer_fields = defer_fields or []

    def apply(self, query: Select) -> Select:
        """Apply configured loading strategies to the SQLAlchemy Select statement."""
        for rel in self.selectin_relationships:
            query = query.options(selectinload(rel))

        for rel in self.joined_relationships:
            query = query.options(joinedload(rel))

        for rel in self.contains_eager_relationships:
            query = query.options(contains_eager(rel))

        if self.load_only_fields:
            query = query.options(load_only(*self.load_only_fields))

        for field in self.defer_fields:
            query = query.options(defer(field))

        return query
