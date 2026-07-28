"""
EAIMOS Feature Flag Service (Sprint 12)
========================================
Service Layer managing enterprise feature toggles and rollouts.
"""

import logging
import uuid
from typing import Any, Dict, Optional, Union

from api.models.feature_flags import FeatureFlag
from api.repositories.base import BaseRepository
from api.services.base import ServiceContext, ServiceResult
from api.services.infrastructure.cache_keys import feature_flag_cache_key
from api.services.infrastructure.dtos import CreateFeatureFlagDTO, FeatureFlagResponseDTO
from api.services.infrastructure.events import FeatureFlagEvaluated
from api.services.infrastructure.mappers import feature_flag_to_response_dto
from api.services.infrastructure.policies import InfrastructurePolicy

logger = logging.getLogger("eaimos.infrastructure.feature_flag")


class _FeatureFlagRepository(BaseRepository[FeatureFlag]):
    def __init__(self) -> None:
        super().__init__(FeatureFlag)

    async def get_by_name(self, session: Any, name: str) -> Optional[FeatureFlag]:
        from sqlalchemy import select
        stmt = select(FeatureFlag).where(FeatureFlag.name == name)
        result = await session.execute(stmt)
        return result.scalars().first()


class FeatureFlagService:
    """Enterprise Feature Toggles, Percentage Rollouts and Strategy Evaluation Service."""

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

    async def create_flag(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreateFeatureFlagDTO,
    ) -> ServiceResult[FeatureFlagResponseDTO]:
        try:
            InfrastructurePolicy.can_manage_feature_flags(self.authorizer, ctx, org_id)

            async with self.uow_service:
                repo = _FeatureFlagRepository()
                # Check duplicate
                existing = await repo.get_by_name(self.uow_service.session, dto.key)
                if existing:
                    from api.services.base.service_exceptions import ValidationError
                    raise ValidationError(
                        message=f"Feature flag with key '{dto.key}' already exists.",
                        field_errors=[{"field": "key", "message": "Duplicate feature flag key"}],
                    )

                data: Dict[str, Any] = {
                    "name": dto.key,
                    "display_name": dto.name,
                    "is_enabled_globally": dto.is_enabled,
                    "rollout_percentage": 0,
                    "metadata_json": {"strategy": dto.strategy},
                }

                flag = await repo.create(
                    session=self.uow_service.session,
                    obj_in=data,
                    actor_id=ctx.get_user_id_uuid(),
                )

            response = feature_flag_to_response_dto(flag)
            await self.cache.set(feature_flag_cache_key(dto.key), response.is_enabled)
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_flag failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def evaluate_flag(
        self,
        ctx: ServiceContext,
        flag_key: str,
    ) -> ServiceResult[bool]:
        try:
            # 1. Check cache first
            cache_key = feature_flag_cache_key(flag_key)
            cached_val = await self.cache.get(cache_key)
            if cached_val is not None:
                if self.dispatcher:
                    await self.dispatcher.publish(
                        FeatureFlagEvaluated(
                            aggregate_id=flag_key,
                            tenant_id=ctx.get_org_id_str(),
                            actor_id=ctx.get_user_id_str(),
                            correlation_id=ctx.correlation_id,
                            flag_key=flag_key,
                            is_enabled=bool(cached_val),
                        )
                    )
                return ServiceResult.ok(data=bool(cached_val))

            # 2. Fetch database
            async with self.uow_service:
                repo = _FeatureFlagRepository()
                flag = await repo.get_by_name(self.uow_service.session, flag_key)
                if not flag:
                    # Default fallback to False
                    return ServiceResult.ok(data=False)

                is_enabled = flag.is_enabled_globally

            # 3. Cache the value and dispatch event
            await self.cache.set(cache_key, is_enabled)

            if self.dispatcher:
                await self.dispatcher.publish(
                    FeatureFlagEvaluated(
                        aggregate_id=flag_key,
                        tenant_id=ctx.get_org_id_str(),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        flag_key=flag_key,
                        is_enabled=is_enabled,
                    )
                )

            return ServiceResult.ok(data=is_enabled)

        except Exception as exc:
            logger.error(f"evaluate_flag failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
