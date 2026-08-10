"""
Email Log Model
===============
Logs every transactional email delivery attempt.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Integer, Float, DateTime, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from api.database.base import Base


class EmailLog(Base):
    """
    Email logs ledger to track delivery telemetry and correlation metadata.
    """
    __tablename__ = "email_logs"

    __table_args__ = (
        Index("idx_email_logs_recipient", "recipient"),
        Index("idx_email_logs_status", "status"),
        Index("idx_email_logs_correlation_id", "correlation_id"),
        Index("idx_email_logs_created_at", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    recipient: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    template: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="QUEUED")  # QUEUED, SENT, FAILED
    retries: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="resend")
    latency: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # in seconds
    correlation_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
