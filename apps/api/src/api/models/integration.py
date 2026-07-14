"""
Integration Platform Models
============================
Integration           — Third-party integration registration per org
IntegrationCredential — Encrypted OAuth tokens / API keys storage
SyncJob               — Record of a data sync operation
Notification          — In-app notification delivery
NotificationPreference — User notification preferences per channel
"""
import enum
import uuid
from typing import Optional, List
from sqlalchemy import (
    ForeignKey, String, Text, Boolean, Integer, Enum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


# ─── Integration Models ───────────────────────────────────────────────────────

class IntegrationProvider(str, enum.Enum):
    SLACK = "SLACK"
    GOOGLE_DRIVE = "GOOGLE_DRIVE"
    GMAIL = "GMAIL"
    GOOGLE_CALENDAR = "GOOGLE_CALENDAR"
    HUBSPOT = "HUBSPOT"
    SALESFORCE = "SALESFORCE"
    WEBHOOK = "WEBHOOK"
    CUSTOM_API = "CUSTOM_API"


class IntegrationStatus(str, enum.Enum):
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    PENDING_AUTH = "PENDING_AUTH"


class Integration(Base):
    """
    An activated third-party integration within an organization.
    """
    __tablename__ = "integrations"
    __table_args__ = (
        Index("ix_integrations_org_id", "organization_id"),
        Index("ix_integrations_provider", "provider"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    provider: Mapped[IntegrationProvider] = mapped_column(
        Enum(IntegrationProvider), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[IntegrationStatus] = mapped_column(
        Enum(IntegrationStatus), default=IntegrationStatus.PENDING_AUTH, nullable=False
    )
    # Integration-specific configuration (webhook URL, scopes, etc.)
    config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # OAuth state / health metadata
    last_synced_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    credentials: Mapped[Optional["IntegrationCredential"]] = relationship(
        "IntegrationCredential", back_populates="integration",
        uselist=False, cascade="all, delete-orphan"
    )
    sync_jobs: Mapped[List["SyncJob"]] = relationship(
        "SyncJob", back_populates="integration", cascade="all, delete-orphan"
    )


class IntegrationCredential(Base):
    """
    Encrypted credential storage for an integration.
    In production: values should be encrypted at rest (AES-256).
    """
    __tablename__ = "integration_credentials"
    __table_args__ = (
        Index("ix_integration_credentials_integration_id", "integration_id"),
    )

    integration_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("integrations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    # OAuth fields
    access_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    token_expiry: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # API key based auth
    api_key: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Additional provider-specific credential data
    extra: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    integration: Mapped["Integration"] = relationship(
        "Integration", back_populates="credentials"
    )


class SyncJob(Base):
    """
    Records of data sync operations triggered for an integration.
    """
    __tablename__ = "sync_jobs"
    __table_args__ = (
        Index("ix_sync_jobs_integration_id", "integration_id"),
        Index("ix_sync_jobs_org_id", "organization_id"),
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
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    records_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    integration: Mapped["Integration"] = relationship("Integration", back_populates="sync_jobs")


# ─── Notification Models ──────────────────────────────────────────────────────

class NotificationChannel(str, enum.Enum):
    IN_APP = "IN_APP"
    EMAIL = "EMAIL"
    SLACK = "SLACK"
    WEBHOOK = "WEBHOOK"


class NotificationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Notification(Base):
    """
    An in-platform notification delivered to a user.
    """
    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id", "user_id"),
        Index("ix_notifications_org_id", "organization_id"),
        Index("ix_notifications_is_read", "is_read"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), default=NotificationChannel.IN_APP, nullable=False
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority), default=NotificationPriority.MEDIUM, nullable=False
    )
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Event type for categorization ("agent_completed", "campaign_launched", etc.)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Deep-link action URL
    action_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Extra metadata
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class NotificationPreference(Base):
    """
    Per-user, per-channel notification preferences.
    """
    __tablename__ = "notification_preferences"
    __table_args__ = (
        Index("ix_notification_prefs_user_id", "user_id"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    channel: Mapped[NotificationChannel] = mapped_column(
        Enum(NotificationChannel), nullable=False
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Event types to mute (JSON array of event_type strings)
    muted_event_types: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
