"""
Prompt A/B Testing Models — Sprint 4
======================================
Provides A/B testing infrastructure for prompt performance optimization.

Tables:
- prompt_ab_tests        : A/B test campaign definitions
- prompt_ab_test_results : A/B test execution results (partitioned)

Design Rules:
- A/B tests compare Prompt A vs. Prompt B
- Splits traffic dynamically according to configured split percentage
- Compares latency, cost, and custom evaluation scores
- Results are logged and stored in monthly partitioned tables
"""
import uuid
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    CheckConstraint, DateTime, ForeignKey, Index, Integer, Numeric, String, Text, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

if TYPE_CHECKING:
    from api.models.prompt import Prompt
    from api.models.user import User


class PromptABTest(Base):
    """
    A/B test campaign comparing two prompts or two versions of a prompt.
    """
    __tablename__ = "prompt_ab_tests"

    __table_args__ = (
        CheckConstraint(
            "traffic_split_pct BETWEEN 0 AND 100",
            name="ck_prompt_ab_tests_traffic_split_pct",
        ),
        CheckConstraint(
            "status IN ('DRAFT', 'RUNNING', 'COMPLETED', 'CANCELLED')",
            name="ck_prompt_ab_tests_status",
        ),
        Index("idx_prompt_ab_tests_org_status", "organization_id", "status"),
        Index("idx_prompt_ab_tests_prompt_a", "prompt_a_id"),
        Index("idx_prompt_ab_tests_prompt_b", "prompt_b_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # ── Variants ──────────────────────────────────────────────────────────────
    prompt_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="CASCADE"),
        nullable=False,
    )
    prompt_a_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prompt_b_version: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # ── Split & Metrics ───────────────────────────────────────────────────────
    traffic_split_pct: Mapped[int] = mapped_column(
        Integer, nullable=False, default=50, server_default="50",
        comment="Percentage of traffic routed to Variant A (0-100)",
    )
    metric: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Evaluation metric: success_rate | latency | cost | score",
    )

    # ── Lifecycle ─────────────────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="DRAFT", server_default="DRAFT"
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # ── Winning Variant ───────────────────────────────────────────────────────
    winner_prompt_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompts.id", ondelete="SET NULL"),
        nullable=True,
    )
    confidence_level: Mapped[Optional[float]] = mapped_column(
        Numeric(5, 2), nullable=True, comment="Statistical confidence level"
    )
    min_sample_size: Mapped[int] = mapped_column(
        Integer, nullable=False, default=100, server_default="100",
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    results: Mapped[List["PromptABTestResult"]] = relationship(
        "PromptABTestResult", back_populates="ab_test", cascade="all, delete-orphan"
    )


class PromptABTestResult(Base):
    """
    Log of each execution variant routed during an active A/B test.
    Partitioned monthly.
    """
    __tablename__ = "prompt_ab_test_results"

    __table_args__ = (
        CheckConstraint(
            "variant IN ('A', 'B')",
            name="ck_prompt_ab_test_results_variant",
        ),
        Index("idx_prompt_ab_test_res_test_var", "ab_test_id", "variant"),
        Index("idx_prompt_ab_test_res_created", "created_at"),
    )

    ab_test_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_ab_tests.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    variant: Mapped[str] = mapped_column(
        String(1), nullable=False, comment="'A' or 'B'"
    )
    execution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("prompt_executions.id", ondelete="SET NULL"),
        nullable=True,
    )
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cost_usd: Mapped[float] = mapped_column(Numeric(12, 8), nullable=False, default=0.0)
    success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    ab_test: Mapped[PromptABTest] = relationship("PromptABTest", back_populates="results")
