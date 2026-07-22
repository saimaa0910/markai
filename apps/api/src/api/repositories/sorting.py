"""
EAIMOS Sort Utilities
======================
Dynamic sorting compilation for SQLAlchemy queries.
"""

from enum import Enum
from typing import Any, List, Type
from pydantic import BaseModel, Field
from sqlalchemy import Select, asc, desc, nulls_first, nulls_last
from sqlalchemy.orm import InstrumentedAttribute


class SortDirection(str, Enum):
    ASC = "asc"
    DESC = "desc"


class SortParam(BaseModel):
    """Declarative specification for query ordering."""

    field: str = Field(description="Name of the model attribute to sort by")
    direction: SortDirection = Field(default=SortDirection.ASC, description="Sort direction: asc or desc")
    nulls_first: bool = Field(default=False, description="Place NULL values first if True")


def apply_sorting(
    query: Select,
    model: Type[Any],
    sort_params: List[SortParam],
    default_sort_field: str = "created_at",
    default_direction: SortDirection = SortDirection.DESC,
) -> Select:
    """
    Apply a sequence of SortParam objects to a SQLAlchemy select query.

    Args:
        query: SQLAlchemy Select statement.
        model: Target model class.
        sort_params: List of SortParam objects.
        default_sort_field: Fallback field if sort_params is empty.
        default_direction: Fallback direction if sort_params is empty.

    Returns:
        Updated Select statement with order_by clauses added.
    """
    order_clauses = []

    if sort_params:
        for param in sort_params:
            if hasattr(model, param.field):
                col: InstrumentedAttribute = getattr(model, param.field)
                clause = asc(col) if param.direction == SortDirection.ASC else desc(col)
                if param.nulls_first:
                    clause = nulls_first(clause)
                else:
                    clause = nulls_last(clause)
                order_clauses.append(clause)

    if not order_clauses and hasattr(model, default_sort_field):
        default_col: InstrumentedAttribute = getattr(model, default_sort_field)
        clause = asc(default_col) if default_direction == SortDirection.ASC else desc(default_col)
        order_clauses.append(clause)

    if order_clauses:
        query = query.order_by(*order_clauses)

    return query
