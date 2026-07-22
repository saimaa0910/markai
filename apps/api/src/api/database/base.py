"""
EAIMOS Database Base Model
==========================
Enterprise-grade base class with:
- UUID primary key
- Audit timestamps (created_at, updated_at)
- Actor tracking (created_by, updated_by) as UUID FK references
- Soft delete (deleted_at)
- Optimistic locking (version)
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in EAIMOS.

    Standard columns applied to every table:
    - id            : UUID primary key (gen_random_uuid equivalent)
    - created_at    : Server-side NOW() on insert
    - updated_at    : Server-side NOW(), auto-updated on change
    - created_by    : UUID of the user who created this record (nullable)
    - updated_by    : UUID of the user who last updated this record (nullable)
    - deleted_at    : Soft-delete timestamp; NULL = active record
    - version       : Optimistic-locking counter (incremented on every UPDATE)

    Multi-tenancy: all tenant-owned subclasses must add `organization_id`.
    Soft delete:  filter `WHERE deleted_at IS NULL` for active records.
    Optimistic lock: compare `version` on UPDATE, increment atomically.
    """

    # ── Primary Key ──────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        nullable=False,
    )

    # ── Audit Timestamps ─────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=False,  # individual models add compound indexes
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Soft Delete ───────────────────────────────────────────────────────────
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    # ── Actor Tracking (UUID strings for cross-DB compat) ────────────────────
    # NOTE: stored as nullable VARCHAR to avoid circular FK issues at the base
    # level. Individual models that need hard FK enforcement add their own
    # created_by / updated_by columns with proper FK declarations.
    created_by: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        default=None,
    )

    updated_by: Mapped[Optional[str]] = mapped_column(
        nullable=True,
        default=None,
    )

    # ── Optimistic Locking ────────────────────────────────────────────────────
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        server_default="1",
    )
