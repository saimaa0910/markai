import uuid
import datetime
from typing import Optional, List
from sqlalchemy import ForeignKey, String, Integer, DateTime, Text, Numeric, JSON, Table, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


# Junction table for collections and image library
image_collection_items = Table(
    "ai_image_collection_items",
    Base.metadata,
    Column("collection_id", UUID(as_uuid=True), ForeignKey("ai_image_collections.id", ondelete="CASCADE"), primary_key=True),
    Column("image_library_id", UUID(as_uuid=True), ForeignKey("ai_image_library.id", ondelete="CASCADE"), primary_key=True),
)


class AIImageCollection(Base):
    __tablename__ = "ai_image_collections"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    images: Mapped[List["AIImageLibrary"]] = relationship(
        "AIImageLibrary",
        secondary=image_collection_items,
        back_populates="collections"
    )


class AIImageLibrary(Base):
    __tablename__ = "ai_image_library"

    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    negative_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    seed: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cfg_scale: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
    steps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="COMPLETED", nullable=False)  # QUEUED | RUNNING | COMPLETED | FAILED | CANCELLED
    soft_deleted_at: Mapped[Optional[datetime.datetime]] = mapped_column(DateTime, nullable=True)

    # Foreign Keys
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="SET NULL"),
        nullable=True,
    )
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    file_asset_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("file_assets.id", ondelete="CASCADE"),
        nullable=True,
    )
    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_image_library.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Extra fields
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    storage_url: Mapped[str] = mapped_column(String(512), nullable=False)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow, nullable=False
    )

    # Relationships
    file_asset = relationship("FileAsset", backref="image_library_items")
    parent = relationship("AIImageLibrary", remote_side="AIImageLibrary.id", backref="versions")
    collections: Mapped[List[AIImageCollection]] = relationship(
        "AIImageCollection",
        secondary=image_collection_items,
        back_populates="images"
    )
