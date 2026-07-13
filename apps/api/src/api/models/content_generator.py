import uuid
from typing import List, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.content_variant import ContentVariant


class GeneratedContent(Base):
    __tablename__ = "generated_contents"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    prompt_used: Mapped[str] = mapped_column(Text, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    variants: Mapped[List["ContentVariant"]] = relationship(
        "ContentVariant",
        back_populates="generated_content",
        cascade="all, delete-orphan",
    )
