"""
EAIMOS Integrations Repository Module — Sprint 10
=================================================
Repository implementations for Integrations models:
Integration, IntegrationCredential, SyncJob, WebhookEndpoint, WebhookDelivery.
"""

from typing import Any, List, Optional
import uuid

from api.models.integration import (
    Integration,
    IntegrationCredential,
    SyncJob,
)
from api.models.integration_webhooks import WebhookEndpoint, WebhookDelivery
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class IntegrationRepository(TenantRepository[Integration]):
    """Data access layer for Organization Integrations."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(Integration, organization_id=organization_id)

    async def get_by_provider(self, session: Any, provider: str) -> Optional[Integration]:
        filters = [FilterParam(field="provider", operator=FilterOperator.EQ, value=provider)]
        return await self.find_one(session=session, filters=filters)


class IntegrationCredentialRepository(TenantRepository[IntegrationCredential]):
    """Data access layer for Integration Credentials."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(IntegrationCredential, organization_id=organization_id)


class SyncJobRepository(TenantRepository[SyncJob]):
    """Data access layer for Data Sync Jobs."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(SyncJob, organization_id=organization_id)


class WebhookEndpointRepository(TenantRepository[WebhookEndpoint]):
    """Data access layer for Webhook Endpoints."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(WebhookEndpoint, organization_id=organization_id)


class WebhookDeliveryRepository(TenantRepository[WebhookDelivery]):
    """Data access layer for Webhook Delivery Logs."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(WebhookDelivery, organization_id=organization_id)
