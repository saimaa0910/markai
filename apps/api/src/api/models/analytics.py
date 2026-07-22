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

class AnalyticsSnapshot(Base):
    """
    Time-series metric aggregations.
    Partitioned monthly.
    """
    __tablename__ = "analytics_snapshots"

    __table_args__ = (
        Index("idx_snapshots_org_metric_period", "organization_id", "metric_name", "period", "period_start"),
        Index("idx_snapshots_module", "organization_id", "module"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    period: Mapped[str] = mapped_column(String(20), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(20, 6), default=0.000000, nullable=False)
    dimensions: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True, default=dict)
    metadata_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class AnalyticsDashboard(Base):
    """
    Organization customizable dashboards.
    """
    __tablename__ = "analytics_dashboards"

    __table_args__ = (
        Index("idx_analytics_dashboards_org", "organization_id"),
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
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    layout_config: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    filters: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    refresh_interval_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    widgets: Mapped[List["AnalyticsWidget"]] = relationship("AnalyticsWidget", back_populates="dashboard", cascade="all, delete-orphan")


class AnalyticsWidget(Base):
    """
    Individual widget blocks inside AnalyticsDashboard.
    """
    __tablename__ = "analytics_widgets"

    __table_args__ = (
        Index("idx_analytics_widgets_dash", "dashboard_id"),
    )

    dashboard_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analytics_dashboards.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    widget_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    chart_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    position_x: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    position_y: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    size_w: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    size_h: Mapped[int] = mapped_column(Integer, default=4, nullable=False)

    dashboard: Mapped[AnalyticsDashboard] = relationship("AnalyticsDashboard", back_populates="widgets")


class AnalyticsReport(Base):
    """
    Report generation blueprint parameters.
    """
    __tablename__ = "analytics_reports"

    __table_args__ = (
        Index("idx_analytics_reports_org", "organization_id"),
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
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_config: Mapped[dict] = mapped_column(JSONB, nullable=False)
    schedule_cron: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_run_status: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    output_format: Mapped[str] = mapped_column(String(20), default="TABLE", nullable=False)


class AnalyticsReportRun(Base):
    """
    Audit execution log of reports.
    """
    __tablename__ = "analytics_report_runs"

    __table_args__ = (
        Index("idx_report_runs_report", "report_id"),
        Index("idx_report_runs_org", "organization_id"),
    )

    report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analytics_reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    run_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class AnalyticsEvent(Base):
    """
    Raw operational interaction event stream.
    """
    __tablename__ = "analytics_events"

    __table_args__ = (
        Index("idx_analytics_events_org_type", "organization_id", "event_type", "created_at"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)


class AnalyticsFunnel(Base):
    """
    Dynamic marketing/conversion funnels.
    """
    __tablename__ = "analytics_funnels"

    __table_args__ = (
        Index("idx_funnels_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    steps: Mapped[List["AnalyticsFunnelStep"]] = relationship("AnalyticsFunnelStep", back_populates="funnel", cascade="all, delete-orphan")


class AnalyticsFunnelStep(Base):
    """
    Sequence events forming a funnel conversion path.
    """
    __tablename__ = "analytics_funnel_steps"

    __table_args__ = (
        Index("idx_funnel_steps_funnel", "funnel_id"),
    )

    funnel_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analytics_funnels.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    matching_rules: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    funnel: Mapped[AnalyticsFunnel] = relationship("AnalyticsFunnel", back_populates="steps")


class AnalyticsCohort(Base):
    """
    Cohort cohorts segmentation rules.
    """
    __tablename__ = "analytics_cohorts"

    __table_args__ = (
        Index("idx_cohorts_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cohort_type: Mapped[str] = mapped_column(String(50), default="ACQUISITION", nullable=False)
    matching_criteria: Mapped[dict] = mapped_column(JSONB, nullable=False)
