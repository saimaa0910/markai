"""
EAIMOS Notification Service (Sprint 12)
========================================
Service Layer managing Notification Dispatching and Channel Delivery.
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from api.services.base import ServiceContext, ServiceResult
from api.services.infrastructure.dtos import SendNotificationDTO, NotificationResponseDTO
from api.services.infrastructure.events import NotificationDispatched
from api.services.infrastructure.policies import InfrastructurePolicy
from api.services.infrastructure.validators import validate_notification_channel

logger = logging.getLogger("eaimos.infrastructure.notification")


class NotificationService:
    """Notification Dispatch and Delivery Engine."""

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

    async def send_notification(
        self,
        ctx: ServiceContext,
        dto: SendNotificationDTO,
    ) -> ServiceResult[NotificationResponseDTO]:
        try:
            org_id = ctx.organization_id or uuid.uuid4()
            InfrastructurePolicy.can_manage_notifications(self.authorizer, ctx, org_id)
            validate_notification_channel(dto.channel)

            notif_id = uuid.uuid4()
            now = datetime.now(timezone.utc)

            # Simulated sending/rendering pipeline
            logger.info(
                f"Sending notification {notif_id} to {dto.recipient} via {dto.channel}: {dto.subject}"
            )

            if self.dispatcher:
                await self.dispatcher.publish(
                    NotificationDispatched(
                        aggregate_id=str(notif_id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        recipient=dto.recipient,
                        channel=dto.channel.upper(),
                        subject=dto.subject,
                    )
                )

            res = NotificationResponseDTO(
                id=notif_id,
                recipient=dto.recipient,
                channel=dto.channel.upper(),
                status="DISPATCHED",
                sent_at=now,
            )

            return ServiceResult.ok(data=res, status_code=201)

        except Exception as exc:
            logger.error(f"send_notification failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
