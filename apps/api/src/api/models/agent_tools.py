"""
Agent Tools and Analytics Models — Sprint 6
===========================================
Defines the tool registry and usage logs/analytics for AI Agents.

Tables:
- agent_tools              : Register of custom/webhook/CRM tools available to agents
- agent_tool_executions    : Audit trail of all tool executions
- agent_knowledge_bindings : Linking agents to knowledge collections
- agent_analytics          : Aggregated usage and cost metrics
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Boolean, CheckConstraint, ForeignKey, Index, Integer, Numeric, String, Text,
    UniqueConstraint, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.agent import AgentDefinition
    from api.models.user import User


class AgentTool(Base):
    """
    Registry of tools/actions AI Agents can execute.
    """
    __tablename__ = "agent_tools"

    __table_args__ = (
        UniqueConstraint("name", "organization_id", name="uq_agent_tools_name_org"),
        Index("idx_agent_tools_org", "organization_id"),
        Index("idx_agent_tools_type", "tool_type"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="NULL = system-level tool, available globally",
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    tool_type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="knowledge | crm | campaign | webhook | api | workflow",
    )
    input_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    output_schema: Mapped[dict] = mapped_column(JSONB, nullable=False)
    endpoint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    auth_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    timeout_seconds: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)


class AgentToolExecution(Base):
    """
    Granular execution audit for agent tool calls.
    """
    __tablename__ = "agent_tool_executions"

    __table_args__ = (
        Index("idx_agent_tool_exec_run", "run_id"),
        Index("idx_agent_tool_exec_org", "organization_id", "created_at"),
    )

    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    tool_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_tools.id", ondelete="SET NULL"),
        nullable=True,
    )
    tool_name: Mapped[str] = mapped_column(String(100), nullable=False)
    call_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    input_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="success", nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AgentKnowledgeBinding(Base):
    """
    Binds an agent to a Knowledge Collection for semantic search RAG retrieval.
    """
    __tablename__ = "agent_knowledge_bindings"

    __table_args__ = (
        UniqueConstraint("agent_id", "collection_id", name="uq_agent_knowledge_binding"),
        Index("idx_agent_kb_agent", "agent_id"),
        Index("idx_agent_kb_collection", "collection_id"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    collection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("knowledge_collections.id", ondelete="CASCADE"),
        nullable=False,
    )
    max_chunks: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    similarity_threshold: Mapped[float] = mapped_column(Numeric(4, 2), default=0.70, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class AgentAnalytics(Base):
    """
    Aggregated operational usage & cost metrics for AI Agents.
    """
    __tablename__ = "agent_analytics"

    __table_args__ = (
        UniqueConstraint("agent_id", name="uq_agent_analytics_agent"),
        Index("idx_agent_analytics_org", "organization_id"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    total_sessions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    successful_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_runs: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_cost_usd: Mapped[float] = mapped_column(Numeric(12, 4), default=0.0000, nullable=False)
    avg_latency_ms: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    avg_iterations: Mapped[float] = mapped_column(Numeric(6, 2), default=0.00, nullable=False)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
