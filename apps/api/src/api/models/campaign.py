import enum
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Numeric, Enum, DateTime, Integer, Index, JSON
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
    __table_args__ = (
        Index("idx_campaigns_org_status", "organization_id", "status"),
        Index("idx_campaigns_org_channel", "organization_id", "channel"),
        Index("idx_campaigns_org_scheduled", "organization_id", "scheduled_for"),
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[CampaignStatus] = mapped_column(
        Enum(CampaignStatus), default=CampaignStatus.DRAFT, nullable=False
    )
    scheduled_for: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    budget: Mapped[float] = mapped_column(
        Numeric(12, 4), default=0.0000, nullable=False
    )
    spent_budget: Mapped[float] = mapped_column(
        Numeric(12, 4), default=0.0000, nullable=False
    )
    currency: Mapped[str] = mapped_column(
        String(3), default="USD", nullable=False
    )
    channel: Mapped[CampaignChannel] = mapped_column(
        Enum(CampaignChannel), nullable=False
    )
    goal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    target_audience_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    team_ids: Mapped[Optional[list[uuid.UUID]]] = mapped_column(JSON, nullable=True)
    tags: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)

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
