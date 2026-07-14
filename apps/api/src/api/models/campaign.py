import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Numeric, Enum, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class CampaignStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SCHEDULED = "SCHEDULED"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    ARCHIVED = "ARCHIVED"


class CampaignChannel(str, enum.Enum):
    EMAIL = "EMAIL"
    SOCIAL = "SOCIAL"
    ADS = "ADS"


class Campaign(Base):
    __tablename__ = "campaigns"

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False
    )
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    budget: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0.00, nullable=False
    )
    channel: Mapped[CampaignChannel] = mapped_column(
        Enum(CampaignChannel), nullable=False
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    template: Mapped[Optional["CampaignTemplate"]] = relationship(
        "CampaignTemplate",
        back_populates="campaign",
        uselist=False,
        cascade="all, delete-orphan",
    )
    analytics: Mapped[Optional["CampaignAnalytics"]] = relationship(
        "CampaignAnalytics",
        back_populates="campaign",
        uselist=False,
        cascade="all, delete-orphan",
    )


class CampaignTemplate(Base):
    __tablename__ = "campaign_templates"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_a: Mapped[str] = mapped_column(Text, nullable=False)
    content_b: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="template"
    )


class CampaignAnalytics(Base):
    __tablename__ = "campaign_analytics"

    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    impressions_a: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_a: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions_a: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    impressions_b: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    clicks_b: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    conversions_b: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    revenue: Mapped[float] = mapped_column(
        Numeric(10, 2), default=0.00, nullable=False
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="analytics"
    )
