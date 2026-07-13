import uuid
from typing import Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.content_generator import GeneratedContent


class ContentVariant(Base):
    __tablename__ = "content_variants"

    generated_content_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("generated_contents.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant_label: Mapped[str] = mapped_column(
        String(10), nullable=False
    )  # 'Variant A', 'Variant B'
    content: Mapped[str] = mapped_column(Text, nullable=False)
    model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[Optional[int]] = mapped_column(
        Integer, nullable=True
    )  # rating from 1 to 5

    # Relationships
    generated_content: Mapped["GeneratedContent"] = relationship(
        "GeneratedContent", back_populates="variants"
    )
