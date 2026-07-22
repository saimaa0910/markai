"""
Security and Compliance Models — Sprint 14
===========================================
Threat response, governance, security auditing, and compliance policy mapping.

Tables:
- security_incidents       : Registry of security incidents/events
- threat_detections        : Logs of suspicious behaviors flagged
- compliance_frameworks    : Compliance standards (SOC2, GDPR, HIPAA)
- compliance_controls      : Specific standard requirements mapped
- compliance_assessments   : Record of audits conducted
- data_classification_rules: Sensitive fields patterns (regex classifications)
- pii_scan_results         : Findings of scans detecting sensitive info in text
- security_alerts          : Alerts dispatched for system threats
- ip_allowlists            : Network IP whitelists
- security_event_log       : Partitioned security auditing trail
"""
import uuid
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    ForeignKey, String, Text, Boolean, Integer, Numeric, JSON, Index, UniqueConstraint, DateTime, Date
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from api.database.base import Base

class SecurityIncident(Base):
    """
    Registry of tracked incidents.
    """
    __tablename__ = "security_incidents"

    __table_args__ = (
        Index("idx_sec_incidents_org", "organization_id"),
        Index("idx_sec_incidents_status", "status"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
        comment="NULL = Platform-wide incident",
    )
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    assigned_to: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    affected_users: Mapped[Optional[list[uuid.UUID]]] = mapped_column(JSONB, nullable=True)
    affected_resources: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    root_cause: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_steps: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    timeline: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class ThreatDetection(Base):
    """
    Threat detections triggered by ML analysis or rule breaches.
    """
    __tablename__ = "threat_detections"

    __table_args__ = (
        Index("idx_threat_detect_org", "organization_id"),
        Index("idx_threat_detect_status", "status"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    detection_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="NEW", nullable=False)
    evidence: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)


class ComplianceFramework(Base):
    """
    Regulatory compliance standards definitions.
    """
    __tablename__ = "compliance_frameworks"

    __table_args__ = (
        UniqueConstraint("name", name="uq_compliance_framework_name"),
    )

    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    controls: Mapped[List["ComplianceControl"]] = relationship("ComplianceControl", back_populates="framework", cascade="all, delete-orphan")


class ComplianceControl(Base):
    """
    Specific control requirements inside a standard.
    """
    __tablename__ = "compliance_controls"

    __table_args__ = (
        UniqueConstraint("framework_id", "code", name="uq_compliance_control_code"),
    )

    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    remediation_guidance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    framework: Mapped[ComplianceFramework] = relationship("ComplianceFramework", back_populates="controls")


class ComplianceAssessment(Base):
    """
    Audit execution log mapped against standards.
    """
    __tablename__ = "compliance_assessments"

    __table_args__ = (
        Index("idx_assessments_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    framework_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("compliance_frameworks.id", ondelete="CASCADE"),
        nullable=False,
    )
    conducted_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(String(20), default="IN_PROGRESS", nullable=False)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    findings: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    next_assessment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)


class DataClassificationRule(Base):
    """
    Regex rules defining data sensitivity categorization.
    """
    __tablename__ = "data_classification_rules"

    __table_args__ = (
        Index("idx_classification_rules_org", "organization_id"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    pattern: Mapped[str] = mapped_column(Text, nullable=False, comment="Regex pattern to scan against")
    classification_level: Mapped[str] = mapped_column(String(50), default="PII", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class PiiScanResult(Base):
    """
    Findings when a text block matches a classification pattern.
    """
    __tablename__ = "pii_scan_results"

    __table_args__ = (
        Index("idx_pii_scans_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    scan_source_type: Mapped[str] = mapped_column(String(100), nullable=False, comment="e.g. document_chunks, prompt_executions")
    scan_source_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    matched_rule_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("data_classification_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    matched_fragments: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)


class SecurityAlert(Base):
    """
    Triggered threat security notifications.
    """
    __tablename__ = "security_alerts"

    __table_args__ = (
        Index("idx_security_alerts_org", "organization_id"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    alert_type: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="MEDIUM", nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class IpAllowlist(Base):
    """
    IP firewall allowlist.
    """
    __tablename__ = "ip_allowlists"

    __table_args__ = (
        Index("idx_ip_allowlists_org", "organization_id"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=False,
    )
    cidr_range: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SecurityEventLog(Base):
    """
    Low latency security logs.
    Partitioned daily.
    """
    __tablename__ = "security_event_log"

    __table_args__ = (
        Index("idx_sec_event_log_org", "organization_id", "created_at"),
        Index("idx_sec_event_log_user", "user_id"),
    )

    organization_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organizations.id", ondelete="CASCADE"),
        nullable=True,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="INFO", nullable=False)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resource_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    resource_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    risk_score: Mapped[Optional[float]] = mapped_column(Numeric(4, 2), nullable=True)
