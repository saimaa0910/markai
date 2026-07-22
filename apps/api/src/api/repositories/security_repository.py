"""
EAIMOS Security Platform Repository Module — Sprint 14
======================================================
Repository implementations for Security models:
SecurityIncident, ThreatDetection, ComplianceAssessment, PiiScanResult, SecurityEventLog.
"""

from typing import Any, List, Optional
import uuid

from api.models.security_platform import (
    SecurityIncident,
    ThreatDetection,
    ComplianceAssessment,
    PiiScanResult,
    SecurityEventLog,
)
from api.repositories.tenant import TenantRepository
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class SecurityIncidentRepository(TenantRepository[SecurityIncident]):
    """Data access layer for Security Incidents."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(SecurityIncident, organization_id=organization_id)


class ThreatDetectionRepository(TenantRepository[ThreatDetection]):
    """Data access layer for AI Threat Detections."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(ThreatDetection, organization_id=organization_id)


class ComplianceAssessmentRepository(TenantRepository[ComplianceAssessment]):
    """Data access layer for Compliance Assessments (SOC2/ISO/GDPR)."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(ComplianceAssessment, organization_id=organization_id)


class PiiScanResultRepository(TenantRepository[PiiScanResult]):
    """Data access layer for PII Redaction/Scan Logs."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(PiiScanResult, organization_id=organization_id)


class SecurityEventLogRepository(BaseRepository[SecurityEventLog]):
    """Data access layer for System-Wide Security Audit Events."""

    def __init__(self) -> None:
        super().__init__(SecurityEventLog)
