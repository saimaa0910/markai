"""
Integration Webhooks and Field Mappings — Sprint 10
===================================================
Provides connector endpoints and sync logging.

Tables:
- webhook_endpoints     : Inbound webhook registrations
- webhook_deliveries     : Logs for outbound webhooks (partitioned)
- webhook_events         : Queue for outbound webhooks
- integration_field_mappings : Key mapper for syncing CRM/Assets
- integration_sync_logs  : Sync diagnostics log
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Text, Boolean, Integer, JSON, Index, UniqueConstraint, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

class WebhookEndpoint(Base):
    """
    Outbound webhook subscriptions.
    """
    __tablename__ = "webhook_endpoints"

    __table_args__ = (
        Index("idx_webhook_endpoints_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    secret: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    event_types: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    headers: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    retry_policy: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    last_delivery_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_delivery_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WebhookEvent(Base):
    """
    Queued events waiting to be dispatched via outbound webhooks.
    """
    __tablename__ = "webhook_events"

    __table_args__ = (
        Index("idx_webhook_events_org", "organization_id"),
        Index("idx_webhook_events_status", "status"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class WebhookDelivery(Base):
    """
    Auditing table for outbound webhook dispatches.
    Partitioned daily.
    """
    __tablename__ = "webhook_deliveries"

    __table_args__ = (
        Index("idx_webhook_deliveries_org", "organization_id", "created_at"),
        Index("idx_webhook_deliveries_endpoint", "endpoint_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    endpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_endpoints.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("webhook_events.id", ondelete="CASCADE"),
        nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    response_status: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    response_body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    next_retry_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class IntegrationFieldMapping(Base):
    """
    Maps third-party keys/fields to EAIMOS internal schemas.
    """
    __tablename__ = "integration_field_mappings"

    __table_args__ = (
        UniqueConstraint("integration_id", "external_field", "internal_field", name="uq_field_mapping"),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_field: Mapped[str] = mapped_column(String(100), nullable=False)
    internal_field: Mapped[str] = mapped_column(String(100), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), default="string", nullable=False)
    default_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class IntegrationSyncLog(Base):
    """
    Granular diagnostic sync log.
    """
    __tablename__ = "integration_sync_logs"

    __table_args__ = (
        Index("idx_sync_logs_org", "organization_id", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
    )
    sync_job_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("sync_jobs.id", ondelete="CASCADE"),
        nullable=True,
    )
    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
