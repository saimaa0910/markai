"""
EAIMOS Observability Service Layer (Sprint 11)
==============================================
Public API for Telemetry Traces, Log Ingestion & Incident Alert services.
"""

from api.services.observability.telemetry_service import TelemetryService
from api.services.observability.log_ingestion_service import LogIngestionService
from api.services.observability.incident_alert_service import IncidentAlertService

from api.services.observability.dtos import (
    RecordTraceDTO,
    TraceResponseDTO,
    IngestLogDTO,
    LogResponseDTO,
    CreateIncidentDTO,
    IncidentResponseDTO,
)

from api.services.observability.events import (
    TraceRecorded,
    LogIngested,
    IncidentCreated,
)

from api.services.observability.dependencies import (
    get_telemetry_service,
    get_log_ingestion_service,
    get_incident_alert_service,
)

__all__ = [
    "TelemetryService",
    "LogIngestionService",
    "IncidentAlertService",
    "RecordTraceDTO",
    "TraceResponseDTO",
    "IngestLogDTO",
    "LogResponseDTO",
    "CreateIncidentDTO",
    "IncidentResponseDTO",
    "get_telemetry_service",
    "get_log_ingestion_service",
    "get_incident_alert_service",
]
