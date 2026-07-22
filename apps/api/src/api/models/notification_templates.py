"""
Notification Templates and Batches Models — Sprint 11
======================================================
Provides notification templates, channels, and batch distributions.

Tables:
- notification_templates  : Jinja2 templates for notifications
- notification_batches    : Async batch jobs
- notification_deliveries : Audited delivery attempts
- notification_digests    : Settings for digest distributions (e.g. daily updates)
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Boolean, Integer, UniqueConstraint, Index, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

class NotificationTemplate(Base):
    """
    Template definition for dynamic notifications per channel.
    """
    __tablename__ = "notification_templates"

    __table_args__ = (
        UniqueConstraint("name", "channel", "organization_id", name="uq_notification_template_key"),
        Index("idx_notification_templates_org", "organization_id"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="NULL = system-wide template",
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    channel: Mapped[str] = mapped_column(String(20), nullable=False, comment="IN_APP | EMAIL | SLACK | SMS")
    title_template: Mapped[str] = mapped_column(String(500), nullable=False, comment="Jinja2 template")
    body_template: Mapped[str] = mapped_column(Text, nullable=False, comment="Jinja2 template")
    subject_template: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class NotificationBatch(Base):
    """
    Groups notifications for batch dispatching.
    """
    __tablename__ = "notification_batches"

    __table_args__ = (
        Index("idx_notification_batches_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    total_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class NotificationDelivery(Base):
    """
    Outbox-auditing ledger of notification dispatches.
    """
    __tablename__ = "notification_deliveries"

    __table_args__ = (
        Index("idx_notification_deliv_org", "organization_id", "created_at"),
        Index("idx_notification_deliv_user", "user_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    notification_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notifications.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class NotificationDigest(Base):
    """
    Accumulates low-priority notifications into a single digest.
    """
    __tablename__ = "notification_digests"

    __table_args__ = (
        Index("idx_notification_digests_user", "user_id"),
    )

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
    frequency: Mapped[str] = mapped_column(String(20), default="DAILY", nullable=False, comment="DAILY | WEEKLY")
    next_send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
