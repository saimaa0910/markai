"""
EAIMOS Observability Interfaces
================================
Protocol declarations for Sprint 11 Observability services.
"""

from typing import Protocol, Union
import uuid
from api.services.base.service_context import ServiceContext
from api.services.base.service_result import ServiceResult
from api.services.observability.dtos import (
    RecordTraceDTO,
    TraceResponseDTO,
    IngestLogDTO,
    LogResponseDTO,
    CreateIncidentDTO,
    IncidentResponseDTO,
)


class ITelemetryService(Protocol):
    async def record_trace(
        self, ctx: ServiceContext, dto: RecordTraceDTO
    ) -> ServiceResult[TraceResponseDTO]: ...


class ILogIngestionService(Protocol):
    async def ingest_log(
        self, ctx: ServiceContext, dto: IngestLogDTO
    ) -> ServiceResult[LogResponseDTO]: ...


class IIncidentAlertService(Protocol):
    async def create_incident(
        self, ctx: ServiceContext, org_id: Union[uuid.UUID, str], dto: CreateIncidentDTO
    ) -> ServiceResult[IncidentResponseDTO]: ...
