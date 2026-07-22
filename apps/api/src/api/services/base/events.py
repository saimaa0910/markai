"""
EAIMOS Domain Events Module
===========================
Defines the base DomainEvent structure and concrete domain event definitions
emitted across all 15 EAIMOS enterprise domains for event-driven architecture, audit logging,
and asynchronous processing via RabbitMQ/event broker.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid
from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base Domain Event model for all enterprise events."""

    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    aggregate_id: Optional[str] = None
    tenant_id: Optional[str] = None
    actor_id: Optional[str] = None
    correlation_id: Optional[str] = None
    version: int = 1
    payload: Dict[str, Any] = Field(default_factory=dict)


class EntityCreated(DomainEvent):
    """Fired whenever a new domain entity is created."""

    event_type: str = "entity.created"
    entity_name: str = ""


class EntityUpdated(DomainEvent):
    """Fired whenever an existing entity is modified."""

    event_type: str = "entity.updated"
    entity_name: str = ""
    changes: Dict[str, Any] = Field(default_factory=dict)


class EntityDeleted(DomainEvent):
    """Fired whenever an entity is soft-deleted or hard-deleted."""

    event_type: str = "entity.deleted"
    entity_name: str = ""
    is_hard_delete: bool = False


class EntityRestored(DomainEvent):
    """Fired whenever a soft-deleted entity is restored."""

    event_type: str = "entity.restored"
    entity_name: str = ""


class WorkflowStarted(DomainEvent):
    """Fired when an enterprise workflow execution commences."""

    event_type: str = "workflow.started"
    workflow_id: str = ""
    execution_id: str = ""


class WorkflowCompleted(DomainEvent):
    """Fired when a workflow execution completes successfully or fails."""

    event_type: str = "workflow.completed"
    workflow_id: str = ""
    execution_id: str = ""
    status: str = "COMPLETED"


class AIRequestCompleted(DomainEvent):
    """Fired when an AI Gateway request resolves."""

    event_type: str = "ai.request_completed"
    provider: str = ""
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_ms: float = 0.0


class PromptPublished(DomainEvent):
    """Fired when a new prompt version is published into production."""

    event_type: str = "prompt.published"
    prompt_id: str = ""
    prompt_version: str = ""


class KnowledgeIndexed(DomainEvent):
    """Fired when document chunks are embedded and indexed in vector storage."""

    event_type: str = "knowledge.indexed"
    document_id: str = ""
    chunk_count: int = 0


class CampaignLaunched(DomainEvent):
    """Fired when a marketing campaign starts distribution."""

    event_type: str = "campaign.launched"
    campaign_id: str = ""
    target_audience_size: int = 0


class InvoicePaid(DomainEvent):
    """Fired when a tenant billing invoice is settled."""

    event_type: str = "billing.invoice_paid"
    invoice_id: str = ""
    amount_cents: int = 0
    currency: str = "USD"


class NotificationSent(DomainEvent):
    """Fired when an outbound notification (email, SMS, webhook) is dispatched."""

    event_type: str = "notification.sent"
    notification_id: str = ""
    channel: str = "EMAIL"
    recipient: str = ""
