"""
CRM Core Models — Sprint 9
============================
Provides pipeline, deals, stages, custom fields, and email subscriptions for the CRM system.

Tables:
- pipelines              : CRM Pipeline definition
- deal_stages            : Progression stages for a pipeline
- deals                  : Revenue opportunities (leads qualified to deals)
- email_subscriptions    : Consent registry for GDPR/CAN-SPAM compliance
- contact_custom_fields  : Schema definitions for custom properties
- contact_custom_values  : Stored values for custom properties
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, Numeric, String, Text,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.organization import Organization
    from api.models.user import User
    from api.models.company import Company
    from api.models.contact import Contact


class Pipeline(Base):
    """
    Pipeline definitions for sales opportunities (deals).
    """
    __tablename__ = "pipelines"

    __table_args__ = (
        Index("idx_pipelines_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)

    # Relationships
    stages: Mapped[List["DealStage"]] = relationship(
        "DealStage", back_populates="pipeline", cascade="all, delete-orphan"
    )
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="pipeline")


class DealStage(Base):
    """
    Individual steps within a sales Pipeline.
    """
    __tablename__ = "deal_stages"

    __table_args__ = (
        Index("idx_deal_stages_pipeline", "pipeline_id"),
    )

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    probability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    pipeline: Mapped[Pipeline] = relationship("Pipeline", back_populates="stages")
    deals: Mapped[List["Deal"]] = relationship("Deal", back_populates="stage")


class Deal(Base):
    """
    Sales opportunities tracking potential revenue.
    """
    __tablename__ = "deals"

    __table_args__ = (
        Index("idx_deals_org", "organization_id"),
        Index("idx_deals_pipeline_stage", "pipeline_id", "stage_id"),
        Index("idx_deals_owner", "owner_id"),
        Index("idx_deals_company", "company_id"),
        Index("idx_deals_contact", "contact_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("pipelines.id", ondelete="CASCADE"),
        nullable=False,
    )
    stage_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deal_stages.id", ondelete="CASCADE"),
        nullable=False,
    )
    company_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="SET NULL"),
        nullable=True,
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )
    owner_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 4), default=0.0000, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="USD", nullable=False)
    probability: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    expected_close_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    close_reason: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lost_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    pipeline: Mapped[Pipeline] = relationship("Pipeline", back_populates="deals")
    stage: Mapped[DealStage] = relationship("DealStage", back_populates="deals")
    company: Mapped[Optional["Company"]] = relationship("Company", back_populates="deals")
    contact: Mapped[Optional["Contact"]] = relationship("Contact", back_populates="deals")


class EmailSubscription(Base):
    """
    Opt-in/Opt-out preferences registry (compliance boundary).
    """
    __tablename__ = "email_subscriptions"

    __table_args__ = (
        UniqueConstraint("organization_id", "email", "list_type", name="uq_email_sub_org_email_list"),
        Index("idx_email_subs_org_email", "organization_id", "email"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="SET NULL"),
        nullable=True,
    )

    email: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), default="SUBSCRIBED", nullable=False,
        comment="SUBSCRIBED | UNSUBSCRIBED | BOUNCED | COMPLAINED",
    )
    subscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unsubscribe_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    list_type: Mapped[str] = mapped_column(
        String(50), default="MARKETING", nullable=False,
        comment="MARKETING | TRANSACTIONAL | PRODUCT",
    )
    consent_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    consent_ip: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    consent_recorded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ContactCustomField(Base):
    """
    Definition of custom fields (custom properties schema) for contacts.
    """
    __tablename__ = "contact_custom_fields"

    __table_args__ = (
        UniqueConstraint("organization_id", "key", name="uq_contact_custom_fields_key_org"),
        Index("idx_custom_fields_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    key: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    field_type: Mapped[str] = mapped_column(
        String(20), default="text", nullable=False,
        comment="text | number | boolean | date | select",
    )
    options: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ContactCustomValue(Base):
    """
    Values matching ContactCustomField definitions per contact.
    """
    __tablename__ = "contact_custom_values"

    __table_args__ = (
        UniqueConstraint("contact_id", "field_id", name="uq_contact_custom_value"),
        Index("idx_custom_values_contact", "contact_id"),
    )

    contact_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contacts.id", ondelete="CASCADE"),
        nullable=False,
    )
    field_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("contact_custom_fields.id", ondelete="CASCADE"),
        nullable=False,
    )
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
