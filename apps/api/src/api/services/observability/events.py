"""
EAIMOS Observability Domain Events
===================================
Domain events for Sprint 11 Observability, Telemetry & Incident Monitoring.
"""

from api.services.base.events import DomainEvent


class TraceRecorded(DomainEvent):
    event_type: str = "observability.trace_recorded"
    trace_id: str = ""
    duration_ms: int = 0


class LogIngested(DomainEvent):
    event_type: str = "observability.log_ingested"
    level: str = ""
    logger: str = ""


class IncidentCreated(DomainEvent):
    event_type: str = "observability.incident_created"
    incident_id: str = ""
    severity: str = ""
