"""
Workflow Engine Models
======================
WorkflowDefinition  — The template/blueprint of a workflow
WorkflowExecution   — A runtime instance of a workflow
WorkflowStep        — Individual step within a workflow execution
"""
import enum
import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    ForeignKey, String, Text, Integer, Enum, Index, JSON, Boolean, UniqueConstraint, DateTime, Numeric
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class WorkflowTrigger(str, enum.Enum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"
    WEBHOOK = "WEBHOOK"
    CAMPAIGN_EVENT = "CAMPAIGN_EVENT"
    CRM_EVENT = "CRM_EVENT"


class WorkflowStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class ExecutionStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    WAITING = "WAITING"


class WorkflowDefinition(Base):
    """
    A declarative workflow blueprint defining steps, agents, tools,
    trigger conditions, and retry policies.
    """
    __tablename__ = "workflow_definitions"
    __table_args__ = (
        Index("ix_workflow_definitions_org_id", "organization_id"),
        Index("ix_workflow_definitions_status", "status"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus), default=WorkflowStatus.DRAFT, nullable=False
    )
    trigger: Mapped[WorkflowTrigger] = mapped_column(
        Enum(WorkflowTrigger), default=WorkflowTrigger.MANUAL, nullable=False
    )
    # JSON DAG of step definitions
    # [{"id": "step_1", "type": "agent_run", "agent_id": "...", "depends_on": []}]
    steps_definition: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Cron expression if trigger == SCHEDULED
    cron_expression: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Webhook configuration if trigger == WEBHOOK
    webhook_config: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Maximum retries on failure
    max_retries: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    # Timeout in seconds
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=3600, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    executions: Mapped[List["WorkflowExecution"]] = relationship(
        "WorkflowExecution", back_populates="workflow", cascade="all, delete-orphan"
    )
    versions: Mapped[List["WorkflowVersion"]] = relationship(
        "WorkflowVersion", back_populates="workflow", cascade="all, delete-orphan"
    )
    triggers: Mapped[List["WorkflowTriggerEntity"]] = relationship(
        "WorkflowTriggerEntity", back_populates="workflow", cascade="all, delete-orphan"
    )
    schedules: Mapped[List["WorkflowSchedule"]] = relationship(
        "WorkflowSchedule", back_populates="workflow", cascade="all, delete-orphan"
    )
    analytics: Mapped[Optional["WorkflowAnalytics"]] = relationship(
        "WorkflowAnalytics", back_populates="workflow", uselist=False, cascade="all, delete-orphan"
    )


class WorkflowVersion(Base):
    """
    Version history for workflow step definitions.
    """
    __tablename__ = "workflow_versions"

    __table_args__ = (
        UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version_num"),
        Index("idx_workflow_ver_workflow", "workflow_id"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    steps_definition: Mapped[dict] = mapped_column(JSON, nullable=False)
    changelog: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="DRAFT", nullable=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    workflow: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="versions")


class WorkflowTriggerEntity(Base):
    """
    Triggers configured to initiate workflow execution.
    """
    __tablename__ = "workflow_triggers"

    __table_args__ = (
        Index("idx_wf_triggers_workflow", "workflow_id"),
        Index("idx_wf_triggers_org", "organization_id"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    webhook_secret: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    webhook_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    conditions: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    workflow: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="triggers")


class WorkflowSchedule(Base):
    """
    Schedules to execute workflows periodically.
    """
    __tablename__ = "workflow_schedules"

    __table_args__ = (
        Index("idx_wf_schedules_workflow", "workflow_id"),
        Index("idx_wf_schedules_next_run", "next_run_at"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(100), default="UTC", nullable=False)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_runs: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    workflow: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="schedules")


class WorkflowAnalytics(Base):
    """
    Aggregated operational analytics for workflows.
    """
    __tablename__ = "workflow_analytics"

    __table_args__ = (
        UniqueConstraint("workflow_id", name="uq_workflow_analytics_wf"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    total_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_executions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_duration_ms: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    p95_duration_ms: Mapped[Optional[float]] = mapped_column(Numeric(10, 2), nullable=True)
    last_execution_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    workflow: Mapped["WorkflowDefinition"] = relationship("WorkflowDefinition", back_populates="analytics")


class WorkflowExecution(Base):
    """
    A runtime instance of a WorkflowDefinition.
    Tracks overall execution state and step progress.
    """
    __tablename__ = "workflow_executions"
    __table_args__ = (
        Index("ix_workflow_executions_workflow_id", "workflow_id"),
        Index("ix_workflow_executions_org_id", "organization_id"),
        Index("ix_workflow_executions_status", "status"),
    )

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False
    )
    # Input context passed into the workflow
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Final output produced by the workflow
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    workflow: Mapped["WorkflowDefinition"] = relationship(
        "WorkflowDefinition", back_populates="executions"
    )
    steps: Mapped[List["WorkflowStep"]] = relationship(
        "WorkflowStep", back_populates="execution", cascade="all, delete-orphan"
    )


class WorkflowStep(Base):
    """
    A single executed step within a WorkflowExecution.
    """
    __tablename__ = "workflow_steps"
    __table_args__ = (
        Index("ix_workflow_steps_execution_id", "execution_id"),
    )

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    step_id: Mapped[str] = mapped_column(String(100), nullable=False)
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[ExecutionStatus] = mapped_column(
        Enum(ExecutionStatus), default=ExecutionStatus.PENDING, nullable=False
    )
    input_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    execution: Mapped["WorkflowExecution"] = relationship(
        "WorkflowExecution", back_populates="steps"
    )
