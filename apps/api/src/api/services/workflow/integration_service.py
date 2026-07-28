"""
EAIMOS Integration Service (Sprint 5)
======================================
Service Layer managing External Integration Webhooks and Event Ingestion.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union
from api.services.base import ServiceContext, ServiceResult
from api.services.workflow.dtos import RegisterWebhookDTO

logger = logging.getLogger("eaimos.workflow.integration")


class IntegrationService:
    """External Webhooks & Connectors Integration Service."""

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

    async def register_webhook(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: RegisterWebhookDTO,
    ) -> ServiceResult[Dict[str, Any]]:
        try:
            webhook_id = uuid.uuid4()
            res = {
                "id": str(webhook_id),
                "organization_id": str(org_id),
                "name": dto.name,
                "target_url": dto.target_url,
                "events": dto.events,
                "is_active": True,
            }
            return ServiceResult.ok(data=res, status_code=201)

        except Exception as exc:
            logger.error(f"register_webhook failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
