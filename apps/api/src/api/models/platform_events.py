"""
Platform Events Model — Sprint 1 (Core Platform)
=================================================
Immutable domain event log implementing event sourcing compatibility.
Every significant state change in EAIMOS emits a platform event.

Design Rules:
- APPEND-ONLY — no UPDATE, no DELETE
- Partitioned by created_at (monthly) via pg_partman
- payload is JSONB for full-fidelity event capture
- idempotency_key prevents duplicate events (at-least-once delivery)
- Producers: all modules
- Consumers: analytics, notifications, Databricks CDC, audit
- Retention: 1 year hot, 5 years cold (Databricks)

Databricks:
- Bronze : bronze.platform_events_raw (streaming CDC)
- Silver : silver.fact_platform_events (parsed, typed)
- Gold   : gold.event_funnel_analysis
"""
import uuid
from typing import Optional
from sqlalchemy import (
    ForeignKey, Index, Integer, String, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from api.database.base import Base


class PlatformEvent(Base):
    """
    Immutable domain event record.

    Every business-significant action emits a PlatformEvent:
    - OrganizationCreated, UserRegistered, PromptExecuted, DealWon, InvoicePaid

    Event sourcing compatibility:
    - aggregate_type + aggregate_id = the entity that changed
    - event_version = payload schema version (for future migration)
    - source = the service/module that produced this event
    """
    __tablename__ = "platform_events"

    # NOTE: This table is PARTITIONED BY RANGE (created_at) in production.
    # The migration creates the parent table + initial partitions.
    # pg_partman handles ongoing partition creation.

    __table_args__ = (
        Index("idx_platform_events_org_id", "organization_id"),
        Index("idx_platform_events_aggregate", "aggregate_type", "aggregate_id"),
        Index("idx_platform_events_event_type", "event_type"),
        Index("idx_platform_events_created_at", "created_at"),
        # Partial unique on idempotency_key (only when set)
        Index(
            "idx_platform_events_idempotency",
            "idempotency_key",
            unique=True,
            postgresql_where="idempotency_key IS NOT NULL",
        ),
    )

    # ── Tenant Scope ──────────────────────────────────────────────────────────
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        comment="NULL = platform-level event (not org-specific)",
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Actor who triggered this event (NULL = system-generated)",
    )

    # ── Event Classification ──────────────────────────────────────────────────
    event_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="PascalCase event name e.g. OrganizationCreated, PromptExecuted",
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Entity type e.g. Organization, Prompt, Campaign, Deal",
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False,
        comment="ID of the entity that changed",
    )

    # ── Payload ───────────────────────────────────────────────────────────────
    payload: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Full event payload — versioned JSON schema",
    )
    event_metadata: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True, default=dict, server_default="{}",
        comment="Correlation IDs, trace context, request metadata",
    )

    # ── Schema Version ────────────────────────────────────────────────────────
    event_version: Mapped[int] = mapped_column(
        Integer, nullable=False, default=1, server_default="1",
        comment="Payload schema version for backwards-compatible migrations",
    )

    # ── Deduplication ─────────────────────────────────────────────────────────
    idempotency_key: Mapped[Optional[str]] = mapped_column(
        String(128), nullable=True,
        comment="Deduplication key for at-least-once delivery guarantee",
    )

    # ── Producer ──────────────────────────────────────────────────────────────
    source: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Originating service/module e.g. prompt, agent, crm, billing",
    )


class AuditLog(Base):
    """
    Platform-wide tamper-evident audit trail for compliance and forensics.

    Compliance Requirements:
    - 7-year retention (SOC2, GDPR, HIPAA)
    - IMMUTABLE: no UPDATE, no DELETE
    - Partitioned quarterly for retention management

    Captures:
    - Who (actor_id, actor_email, actor_ip)
    - What (action: CREATED/UPDATED/DELETED/ACCESSED/EXPORTED)
    - Which (entity_type + entity_id)
    - Before/after state (before_state, after_state, diff)
    - When (created_at)
    - Risk level (low / medium / high / critical)

    Databricks:
    - Bronze: bronze.audit_logs_raw
    - Gold:   gold.compliance_audit_summary
    """
    __tablename__ = "audit_logs"

    __table_args__ = (
        Index("idx_audit_logs_org_id", "organization_id"),
        Index("idx_audit_logs_actor_id", "actor_id"),
        Index("idx_audit_logs_entity", "entity_type", "entity_id"),
        Index("idx_audit_logs_action", "action"),
        Index("idx_audit_logs_created_at", "created_at"),
        Index("idx_audit_logs_risk_level", "risk_level"),
    )

    # ── Tenant ────────────────────────────────────────────────────────────────
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="SET NULL"),
        nullable=True,
        comment="NULL = platform-level action",
    )

    # ── Actor (denormalized for forensics even if user deleted) ───────────────
    actor_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    actor_email: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True,
        comment="Denormalized — preserved even after user deletion",
    )
    actor_ip: Mapped[Optional[str]] = mapped_column(
        String(45), nullable=True, comment="IPv4 or IPv6"
    )
    actor_user_agent: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )

    # ── Target ────────────────────────────────────────────────────────────────
    entity_type: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Table/entity name e.g. prompts, users, campaigns",
    )
    entity_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True,
        comment="ID of the record that was acted upon",
    )
    action: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="CREATED | UPDATED | DELETED | ACCESSED | EXPORTED | RESTORED | PURGED",
    )
    description: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True, comment="Human-readable summary of the action"
    )

    # ── State Snapshots ───────────────────────────────────────────────────────
    before_state: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Serialized entity state BEFORE the action"
    )
    after_state: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Serialized entity state AFTER the action"
    )
    diff: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True, comment="Delta: only changed fields"
    )

    # ── Correlation ───────────────────────────────────────────────────────────
    request_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="HTTP request correlation ID"
    )
    session_id: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, comment="User session ID"
    )

    # ── Risk Classification ───────────────────────────────────────────────────
    risk_level: Mapped[str] = mapped_column(
        String(20), nullable=False, default="low", server_default="low",
        comment="low | medium | high | critical",
    )
