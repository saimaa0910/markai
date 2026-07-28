"""
EAIMOS Log Ingestion Service (Sprint 11)
=========================================
Service Layer managing Centralized Structured Log Ingestion.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from api.services.base import ServiceContext, ServiceResult
from api.services.observability.dtos import IngestLogDTO, LogResponseDTO
from api.services.observability.events import LogIngested
from api.services.observability.validators import validate_log_level_supported

logger = logging.getLogger("eaimos.observability.logging")


class LogIngestionService:
    """Structured Logging & Correlation Binding Service."""

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

    async def ingest_log(
        self,
        ctx: ServiceContext,
        dto: IngestLogDTO,
    ) -> ServiceResult[LogResponseDTO]:
        try:
            validate_log_level_supported(dto.level)
            log_id = uuid.uuid4()
            now = datetime.now(timezone.utc)

            res_dto = LogResponseDTO(
                id=log_id,
                timestamp=now,
                level=dto.level.upper(),
                logger=dto.logger,
                message=dto.message,
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    LogIngested(
                        aggregate_id=str(log_id),
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        level=dto.level.upper(),
                        logger=dto.logger,
                    )
                )

            return ServiceResult.ok(data=res_dto, status_code=201)

        except Exception as exc:
            logger.error(f"ingest_log failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
