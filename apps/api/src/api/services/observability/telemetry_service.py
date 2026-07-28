"""
EAIMOS Telemetry Service (Sprint 11)
=====================================
Service Layer managing Distributed OpenTelemetry Traces & Spans.
"""

import logging
import uuid
from typing import Any, Dict, Optional

from api.models.observability import AITrace
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.observability.cache_keys import trace_cache_key
from api.services.observability.dtos import RecordTraceDTO, TraceResponseDTO
from api.services.observability.events import TraceRecorded
from api.services.observability.mappers import trace_to_response_dto

logger = logging.getLogger("eaimos.observability.telemetry")


class _AITraceRepository(BaseRepository[AITrace]):
    def __init__(self) -> None:
        super().__init__(AITrace)


class TelemetryService:
    """OpenTelemetry Tracing & Span Collector Service."""

    def __init__(
        self,
        uow_service: Optional[Any] = None,
        cache_manager: Optional[Any] = None,
        authorizer: Optional[Any] = None,
        dispatcher: Optional[Any] = None,
    ) -> None:
        from api.services.base.dependency_provider import container
        self.uow_service = uow_service or container.create_uow_service()
        self.cache = cache_manager or container.cache
        self.authorizer = authorizer or container.authorizer
        self.dispatcher = dispatcher or container.dispatcher

    async def record_trace(
        self,
        ctx: ServiceContext,
        dto: RecordTraceDTO,
    ) -> ServiceResult[TraceResponseDTO]:
        try:
            duration = int((dto.end_time - dto.start_time).total_seconds() * 1000)

            async with self.uow_service:
                repo = _AITraceRepository()
                data: Dict[str, Any] = {
                    "trace_id": dto.trace_id,
                    "span_id": dto.span_id,
                    "name": dto.name,
                    "organization_id": ctx.get_org_id_str(),
                    "user_id": ctx.get_user_id_str(),
                    "start_time": dto.start_time,
                    "end_time": dto.end_time,
                    "duration_ms": duration,
                    "status": dto.status,
                    "attributes": dto.attributes,
                }

                trace = await repo.create(
                    session=self.uow_service.session,
                    obj_in=data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                if self.dispatcher:
                    await self.dispatcher.publish(
                        TraceRecorded(
                            aggregate_id=str(trace.id),
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            trace_id=dto.trace_id,
                            duration_ms=duration,
                        )
                    )

            response = trace_to_response_dto(trace)
            await self.cache.set(trace_cache_key(dto.trace_id), response.model_dump(mode="json"))
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"record_trace failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
