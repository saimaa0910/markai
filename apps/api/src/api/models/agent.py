"""
AI Agent Platform Models
========================
AgentDefinition  — Registered agent configuration & capabilities
AgentSession     — A running context/conversation with an agent
AgentRun         — Individual execution of an agent (one step)
AgentLog         — Detailed structured log entries for a run
"""
import enum
import uuid
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    ForeignKey, String, Text, Boolean, Integer,
    Enum, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base


class AgentType(str, enum.Enum):
    MARKETING = "MARKETING"
    CONTENT = "CONTENT"
    CAMPAIGN = "CAMPAIGN"
    CRM = "CRM"
    ANALYTICS = "ANALYTICS"
    RESEARCH = "RESEARCH"
    SEO = "SEO"
    WORKFLOW = "WORKFLOW"
    CUSTOM = "CUSTOM"


class AgentStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class AgentRunStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class AgentDefinition(Base):
    """
    Registered AI Agent within an organization.
    Defines the agent's identity, capabilities, tool access, and prompt config.
    """
    __tablename__ = "agent_definitions"
    __table_args__ = (
        Index("ix_agent_definitions_org_id", "organization_id"),
        Index("ix_agent_definitions_type", "agent_type"),
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    agent_type: Mapped[AgentType] = mapped_column(
        Enum(AgentType), default=AgentType.CUSTOM, nullable=False
    )
    status: Mapped[AgentStatus] = mapped_column(
        Enum(AgentStatus), default=AgentStatus.ACTIVE, nullable=False
    )

    # System prompt template
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Optional Prompt Platform template name to load
    prompt_template_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Tool configuration — JSON array of tool names this agent is allowed to use
    # e.g. ["crm_tool", "knowledge_tool", "campaign_tool"]
    allowed_tools: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # LLM configuration overrides (uses AI Gateway defaults if null)
    preferred_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    temperature: Mapped[float] = mapped_column(
        # Using mapped_column with nullable=False needs a default
        nullable=False, default=0.7
    )
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Memory settings
    memory_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    max_memory_items: Mapped[int] = mapped_column(Integer, default=20, nullable=False)

    # Execution limits
    max_iterations: Mapped[int] = mapped_column(Integer, default=10, nullable=False)

    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    sessions: Mapped[List["AgentSession"]] = relationship(
        "AgentSession", back_populates="agent", cascade="all, delete-orphan"
    )


class AgentSession(Base):
    """
    An active conversation context with a specific agent.
    Maintains state, memory context, and links to runs.
    """
    __tablename__ = "agent_sessions"
    __table_args__ = (
        Index("ix_agent_sessions_org_id", "organization_id"),
        Index("ix_agent_sessions_agent_id", "agent_id"),
        Index("ix_agent_sessions_user_id", "user_id"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_definitions.id", ondelete="CASCADE"),
        nullable=False,
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
    # JSON serialized conversation context passed between runs
    context: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    # Relationships
    agent: Mapped["AgentDefinition"] = relationship(
        "AgentDefinition", back_populates="sessions"
    )
    runs: Mapped[List["AgentRun"]] = relationship(
        "AgentRun", back_populates="session", cascade="all, delete-orphan"
    )


class AgentRun(Base):
    """
    A single execution step of an agent within a session.
    Captures the input, output, tool calls, and telemetry.
    """
    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_session_id", "session_id"),
        Index("ix_agent_runs_organization_id", "organization_id"),
        Index("ix_agent_runs_status", "status"),
    )

    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Input from the user
    user_input: Mapped[str] = mapped_column(Text, nullable=False)
    # Final output produced by the agent
    agent_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # Structured plan (JSON) produced by the planner
    plan: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    # Tool calls executed during this run (JSON array)
    tool_calls: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    status: Mapped[AgentRunStatus] = mapped_column(
        Enum(AgentRunStatus), default=AgentRunStatus.PENDING, nullable=False
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Telemetry
    iterations: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    session: Mapped["AgentSession"] = relationship(
        "AgentSession", back_populates="runs"
    )
    logs: Mapped[List["AgentLog"]] = relationship(
        "AgentLog", back_populates="run", cascade="all, delete-orphan"
    )


class AgentLog(Base):
    """
    Granular structured log entry for a single step within an AgentRun.
    """
    __tablename__ = "agent_logs"
    __table_args__ = (
        Index("ix_agent_logs_run_id", "run_id"),
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

    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    # Step type: "thought", "tool_call", "tool_result", "final_answer"
    step_type: Mapped[str] = mapped_column(String(50), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    # Extra structured data (tool name, input, output, etc.)
    meta_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Relationships
    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="logs")
