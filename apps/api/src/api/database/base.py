import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy models in EAIMOS.
    Contains standard audit metadata columns:
    - id (UUID primary key)
    - created_at (Timestamp)
    - updated_at (Timestamp)
    - created_by (String user identifier/UUID)
    - updated_by (String user identifier/UUID)
    - deleted_at (Timestamp for soft delete)
    """

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    created_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    updated_by: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
