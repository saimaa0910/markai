"""
EAIMOS Observability Dependencies
==================================
FastAPI dependency providers for Sprint 11 Observability services.
"""

from api.services.base.dependency_provider import container
from api.services.observability.telemetry_service import TelemetryService
from api.services.observability.log_ingestion_service import LogIngestionService
from api.services.observability.incident_alert_service import IncidentAlertService


def get_telemetry_service() -> TelemetryService:
    return TelemetryService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_log_ingestion_service() -> LogIngestionService:
    return LogIngestionService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_incident_alert_service() -> IncidentAlertService:
    return IncidentAlertService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
