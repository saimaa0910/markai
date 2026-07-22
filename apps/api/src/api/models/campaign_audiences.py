"""
Campaign Audiences and Sends Models — Sprint 8
==============================================
Provides audience segmentation and campaign sends/events log for multi-channel campaigns.

Tables:
- campaign_audiences : Defines target segments
- campaign_events    : Detailed high-volume campaign event log (impression/click/conversion)
- email_sends        : Individual email sends log (partitioned)
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.campaign import Campaign
    from api.models.contact import Contact
    from api.models.user import User


class CampaignAudience(Base):
    """
    Segmentation logic defining which contacts belong to a target audience segment.
    """
    __tablename__ = "campaign_audiences"

    __table_args__ = (
        Index("idx_campaign_audiences_org", "organization_id"),
        Index("idx_campaign_audiences_type", "segment_type"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    segment_type: Mapped[str] = mapped_column(
        String(50), default="STATIC", nullable=False,
        comment="STATIC | DYNAMIC | LOOKALIKE",
    )
    filter_criteria: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    member_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_computed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class CampaignEvent(Base):
    """
    Granular interaction log for campaigns (impressions, clicks, conversions).
    High-volume table partitioned daily.
    """
    __tablename__ = "campaign_events"

    __table_args__ = (
        Index("idx_campaign_events_org_camp", "organization_id", "campaign_id"),
        Index("idx_campaign_events_contact", "contact_id"),
        Index("idx_campaign_events_type", "event_type"),
        Index("idx_campaign_events_created", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="IMPRESSION | CLICK | OPEN | CONVERSION | UNSUBSCRIBE",
    )
    variant: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False)
    revenue_usd: Mapped[Optional[float]] = mapped_column(Numeric(10, 4), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)


class EmailSend(Base):
    """
    Logs individual email delivery attempts.
    Partitioned monthly.
    """
    __tablename__ = "email_sends"

    __table_args__ = (
        Index("idx_email_sends_org_camp", "organization_id", "campaign_id"),
        Index("idx_email_sends_contact", "contact_id"),
        Index("idx_email_sends_status", "status"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )

    to_email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False)
    template_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaign_templates.id", ondelete="SET NULL"),
        nullable=True,
    )
    esp_message_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default="PENDING", nullable=False,
        comment="PENDING | SENT | DELIVERED | BOUNCED | FAILED",
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    opened_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    clicked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    bounced_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    bounce_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    variant: Mapped[Optional[str]] = mapped_column(String(1), nullable=True)
