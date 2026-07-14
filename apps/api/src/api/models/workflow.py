"""
Workflow Engine Models
======================
WorkflowDefinition  — The template/blueprint of a workflow
WorkflowExecution   — A runtime instance of a workflow
WorkflowStep        — Individual step within a workflow execution
"""
import enum
import uuid
from typing import Optional, List
from sqlalchemy import (
    ForeignKey, String, Text, Integer, Enum, Index, JSON, Boolean
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
