import enum
import uuid
from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import ForeignKey, String, Numeric, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.company import Company
    from api.models.contact import Contact
    from api.models.activity import Activity


class LeadStatus(str, enum.Enum):
    NEW = "NEW"
    CONTACTED = "CONTACTED"
    QUALIFIED = "QUALIFIED"
    LOST = "LOST"


class Lead(Base):
    __tablename__ = "leads"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[LeadStatus] = mapped_column(
        Enum(LeadStatus), default=LeadStatus.NEW, nullable=False
    )
    value: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)

    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    contact: Mapped[Optional["Contact"]] = relationship(
        "Contact", back_populates="leads"
    )
    company: Mapped[Optional["Company"]] = relationship(
        "Company", back_populates="leads"
    )
    activities: Mapped[List["Activity"]] = relationship(
        "Activity", back_populates="lead", cascade="all, delete-orphan"
    )
