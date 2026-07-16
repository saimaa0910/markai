import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import ForeignKey, String, Integer, DateTime, Text, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database.base import Base


class AITrace(Base):
    __tablename__ = "ai_traces"

    trace_id: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    span_id: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_span_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="success", nullable=False)  # success, error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attributes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AILog(Base):
    __tablename__ = "ai_logs"

    trace_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    span_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    correlation_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    level: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    logger: Mapped[str] = mapped_column(String(100), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)


class AIIncident(Base):
    __tablename__ = "ai_incidents"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    component: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # redis, gateway, database, celery, scheduler, queue
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # warning, critical, offline, maintenance
    root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    resolution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)  # active, resolved

    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_sec: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class AIAlert(Base):
    __tablename__ = "ai_alerts"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_incidents.id", ondelete="SET NULL"),
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)  # high_latency, worker_failure, redis_down, queue_overflow, etc.
    message: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(50), nullable=False)  # warning, critical
    channels: Mapped[str] = mapped_column(String(255), nullable=False)  # slack, email, webhook, console
    status: Mapped[str] = mapped_column(String(50), default="triggered", nullable=False)  # triggered, sent, failed


class AIPerformanceMetric(Base):
    __tablename__ = "ai_performance_metrics"

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    metric_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    provider: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    model_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    p50: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p90: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p95: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    p99: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    average: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    maximum: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    minimum: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
