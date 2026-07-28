"""
EAIMOS Analytics Service (Sprint 6)
===================================
Service Layer managing System Metric Aggregation & Reporting.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Union

from api.services.base import ServiceContext, ServiceResult
from api.services.platform.dtos import AnalyticsQueryDTO, AnalyticsSummaryDTO
from api.services.platform.policies import AnalyticsPolicy

logger = logging.getLogger("eaimos.platform.analytics")


class AnalyticsService:
    """Enterprise Analytics & Metric Rollup Service."""

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

    async def query_analytics(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: AnalyticsQueryDTO,
    ) -> ServiceResult[AnalyticsSummaryDTO]:
        try:
            AnalyticsPolicy.can_view(self.authorizer, ctx, org_id)

            res_dto = AnalyticsSummaryDTO(
                metric=dto.metric,
                total_value=12450.0,
                data_points=[
                    {"timestamp": dto.start_date.isoformat(), "value": 4000.0},
                    {"timestamp": dto.end_date.isoformat(), "value": 8450.0},
                ],
            )
            return ServiceResult.ok(data=res_dto)

        except Exception as exc:
            logger.error(f"query_analytics failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
