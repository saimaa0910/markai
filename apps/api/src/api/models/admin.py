"""
Platform Control Plane Administration Models — Sprint 15
==========================================================
Control plane administration, maintenance schedules, support workflows, and auditing actions.

Tables:
- system_configurations : Global platform parameters configurations
- maintenance_windows   : Outage schedules planning
- support_tickets       : User ticketing system
- support_ticket_messages: Support conversation logs
- impersonation_logs    : Superuser authentication impersonation auditing (append-only)
- platform_announcements: Global alerts announcements
- admin_action_logs     : Audits logs for changes inside administrative entities
- system_health_snapshots: Performance metrics snapshot logs
- rate_limit_overrides  : Rate limiter custom overrides config
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    ForeignKey, String, Text, Boolean, Integer, Numeric, JSON, Index, UniqueConstraint, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.user import User

class SystemConfiguration(Base):
    """
    Platform configuration key/value pairs.
    """
    __tablename__ = "system_configurations"

    __table_args__ = (
        UniqueConstraint("namespace", "key", name="uq_system_config_namespace_key"),
    )

    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    namespace: Mapped[str] = mapped_column(String(100), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    value_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    data_type: Mapped[str] = mapped_column(String(20), default="string", nullable=False)
    is_encrypted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_readonly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requires_restart: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class SupportTicket(Base):
    """
    User support tickets.
    """
    __tablename__ = "support_tickets"

    __table_args__ = (
        UniqueConstraint("ticket_number", name="uq_support_tickets_number"),
        Index("idx_support_tickets_org", "organization_id"),
        Index("idx_support_tickets_status", "status"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    ticket_number: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    priority: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    satisfaction_score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    messages: Mapped[List["SupportTicketMessage"]] = relationship("SupportTicketMessage", back_populates="ticket", cascade="all, delete-orphan")


class SupportTicketMessage(Base):
    """
    Dialogue logs inside a support ticket.
    """
    __tablename__ = "support_ticket_messages"

    __table_args__ = (
        Index("idx_ticket_msgs_ticket", "ticket_id"),
    )

    ticket_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    attachments: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)

    ticket: Mapped[SupportTicket] = relationship("SupportTicket", back_populates="messages")


class ImpersonationLog(Base):
    """
    Super-admin user impersonation log.
    Append-only auditing trail.
    """
    __tablename__ = "impersonation_logs"

    __table_args__ = (
        Index("idx_impersonation_logs_admin", "admin_user_id"),
        Index("idx_impersonation_logs_user", "impersonated_user_id"),
    )

    admin_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    impersonated_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("support_tickets.id", ondelete="SET NULL"),
        nullable=True,
    )
    session_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_sessions.id", ondelete="SET NULL"),
        nullable=True,
    )
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)


class MaintenanceWindow(Base):
    """
    Scheduled outage slots.
    """
    __tablename__ = "maintenance_windows"

    __table_args__ = (
        Index("idx_maintenance_windows_start", "scheduled_start"),
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="SCHEDULED", nullable=False)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    actual_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    affected_services: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    notification_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class PlatformAnnouncement(Base):
    """
    Broadcast system notifications banner/alerts.
    """
    __tablename__ = "platform_announcements"

    __table_args__ = (
        Index("idx_announcements_range", "starts_at", "ends_at"),
    )

    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    announcement_type: Mapped[str] = mapped_column(String(50), nullable=False)
    target_plans: Mapped[Optional[list[str]]] = mapped_column(JSONB, nullable=True)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ends_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_dismissible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cta_text: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cta_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AdminActionLog(Base):
    """
    Super-admin commands audit log.
    """
    __tablename__ = "admin_action_logs"

    __table_args__ = (
        Index("idx_admin_action_logs_user", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    target_type: Mapped[str] = mapped_column(String(100), nullable=False)
    target_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    before_state: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    after_state: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)


class SystemHealthSnapshot(Base):
    """
    Telemetry platform metrics logging.
    """
    __tablename__ = "system_health_snapshots"

    __table_args__ = (
        Index("idx_health_snapshots_time", "created_at"),
    )

    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(15, 6), nullable=False)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class RateLimitOverride(Base):
    """
    Organization-specific limits overrides.
    """
    __tablename__ = "rate_limit_overrides"

    __table_args__ = (
        UniqueConstraint("organization_id", "endpoint", name="uq_rate_limit_override"),
        Index("idx_rate_limit_overrides_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    endpoint: Mapped[str] = mapped_column(String(255), nullable=False)
    rpm_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    daily_limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
