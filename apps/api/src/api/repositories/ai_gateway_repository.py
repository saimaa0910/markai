"""
EAIMOS AI Gateway Repository Module — Sprint 3
===============================================
Repository implementations for AI Gateway models:
AIProvider, AIModel, AIProviderKey, AIRequest, AIOrgLimit, AIRoutingPolicy, AIRoutingLog, AITokenUsage.
"""

from typing import Any, List, Optional
import uuid

from api.models.ai_platform import (
    AIProvider,
    AIModel,
    AIProviderKey,
    AIRequest,
    AIOrgLimit,
)
from api.models.router import AIRoutingPolicy, AIRoutingLog
from api.models.ai_usage import AITokenUsage
from api.repositories.base import BaseRepository
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class AIProviderRepository(BaseRepository[AIProvider]):
    """Data access layer for LLM/AI Providers."""

    def __init__(self) -> None:
        super().__init__(AIProvider)

    async def get_by_code(self, session: Any, code: str) -> Optional[AIProvider]:
        filters = [FilterParam(field="name", operator=FilterOperator.EQ, value=code)]
        return await self.find_one(session=session, filters=filters)


class AIModelRepository(BaseRepository[AIModel]):
    """Data access layer for registered AI models."""

    def __init__(self) -> None:
        super().__init__(AIModel)

    async def get_by_model_id(self, session: Any, model_id: str) -> Optional[AIModel]:
        filters = [FilterParam(field="model_id", operator=FilterOperator.EQ, value=model_id)]
        return await self.find_one(session=session, filters=filters)


class AIRequestRepository(TenantRepository[AIRequest]):
    """Data access layer for logged AI LLM requests."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AIRequest, organization_id=organization_id)

    async def list_recent_requests(
        self, session: Any, limit: int = 50, offset: int = 0
    ) -> List[AIRequest]:
        return await self.find_many(session=session, limit=limit, offset=offset)


class AITokenUsageRepository(TenantRepository[AITokenUsage]):
    """Data access layer for token usage analytics."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AITokenUsage, organization_id=organization_id)

    async def list_by_model(self, session: Any, model_name: str) -> List[AITokenUsage]:
        filters = [FilterParam(field="model_name", operator=FilterOperator.EQ, value=model_name)]
        return await self.find_many(session=session, filters=filters)


class AIRoutingPolicyRepository(TenantRepository[AIRoutingPolicy]):
    """Data access layer for org routing policies."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AIRoutingPolicy, organization_id=organization_id)
