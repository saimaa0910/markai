"""
EAIMOS Filter Utilities
========================
Dynamic filter compilation for SQLAlchemy queries.
Converts structured filter specifications into type-safe SQLAlchemy expressions.
"""

from enum import Enum
from typing import Any, List, Optional, Type
from pydantic import BaseModel, Field
from sqlalchemy import Select
from sqlalchemy.orm import InstrumentedAttribute


class FilterOperator(str, Enum):
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IN = "in"
    NOT_IN = "not_in"
    LIKE = "like"
    ILIKE = "ilike"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    JSONB_CONTAINS = "jsonb_contains"
    JSONB_HAS_KEY = "jsonb_has_key"


class FilterParam(BaseModel):
    """Declarative specification for a single column query filter."""

    field: str = Field(description="Name of the model attribute to filter by")
    operator: FilterOperator = Field(default=FilterOperator.EQ, description="Filter comparison operator")
    value: Optional[Any] = Field(default=None, description="Comparison value")


def apply_filters(query: Select, model: Type[Any], filters: List[FilterParam]) -> Select:
    """
    Apply a sequence of dynamic FilterParam objects to a SQLAlchemy select query.

    Args:
        query: SQLAlchemy Select statement.
        model: Target model class.
        filters: List of FilterParam objects.

    Returns:
        Updated Select statement with filter clauses added.
    """
    for filt in filters:
        if not hasattr(model, filt.field):
            continue  # Ignore invalid model attributes safely

        column: InstrumentedAttribute = getattr(model, filt.field)
        op = filt.operator
        val = filt.value

        if op == FilterOperator.EQ:
            query = query.where(column == val)
        elif op == FilterOperator.NEQ:
            query = query.where(column != val)
        elif op == FilterOperator.GT:
            query = query.where(column > val)
        elif op == FilterOperator.GTE:
            query = query.where(column >= val)
        elif op == FilterOperator.LT:
            query = query.where(column < val)
        elif op == FilterOperator.LTE:
            query = query.where(column <= val)
        elif op == FilterOperator.IN:
            if isinstance(val, (list, tuple, set)) and len(val) > 0:
                query = query.where(column.in_(val))
        elif op == FilterOperator.NOT_IN:
            if isinstance(val, (list, tuple, set)) and len(val) > 0:
                query = query.where(~column.in_(val))
        elif op == FilterOperator.LIKE:
            query = query.where(column.like(f"%{val}%"))
        elif op == FilterOperator.ILIKE:
            query = query.where(column.ilike(f"%{val}%"))
        elif op == FilterOperator.IS_NULL:
            query = query.where(column.is_(None))
        elif op == FilterOperator.IS_NOT_NULL:
            query = query.where(column.is_not(None))
        elif op == FilterOperator.JSONB_CONTAINS:
            query = query.where(column.contains(val))
        elif op == FilterOperator.JSONB_HAS_KEY:
            query = query.where(column.has_key(str(val)))

    return query
