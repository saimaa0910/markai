"""
EAIMOS Prompt Service (Sprint 3)
==================================
Service Layer managing Prompt Templates, variable extraction/rendering,
version publishing, and collection/folder organization.
"""

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from api.models.prompt import Prompt, PromptCollection, PromptFolder, PromptVariable
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterOperator, FilterParam
from api.services.base import (
    BaseService,
    ConflictError,
    NotFoundError,
    ServiceContext,
    ServiceResult,
)
from api.services.ai.cache_keys import (
    PROMPT_CACHE_TTL,
    invalidate_pattern_for_org_prompts,
    org_prompts_list_key,
    prompt_template_cache_key,
)
from api.services.ai.constants import PROMPT_VAR_REGEX
from api.services.ai.dtos import (
    CreatePromptDTO,
    PromptResponseDTO,
    RenderPromptDTO,
    RenderedPromptResponseDTO,
    UpdatePromptDTO,
)
from api.services.ai.events import (
    PromptTemplateCreated,
    PromptVersionPublished,
)
from api.services.ai.mappers import prompt_to_response_dto, prompts_to_response_list
from api.services.ai.policies import PromptPolicy
from api.services.ai.validators import validate_prompt_template_syntax

logger = logging.getLogger("eaimos.ai.prompt")


class _PromptRepository(BaseRepository[Prompt]):
    def __init__(self) -> None:
        super().__init__(Prompt)


class PromptService:
    """Enterprise Prompt Template Domain Service."""

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

    async def create_prompt(
        self,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
        dto: CreatePromptDTO,
    ) -> ServiceResult[PromptResponseDTO]:
        try:
            PromptPolicy.can_create(self.authorizer, ctx, org_id)

            extracted_vars = validate_prompt_template_syntax(dto.template)
            all_vars = list(set(extracted_vars + (dto.variables or [])))
            org_uuid = uuid.UUID(str(org_id))

            async with self.uow_service:
                repo = _PromptRepository()
                prompt_data: Dict[str, Any] = {
                    "organization_id": org_uuid,
                    "owner_id": ctx.get_user_id_uuid(),
                    "title": dto.title,
                    "template": dto.template,
                    "description": dto.description,
                    "collection_id": uuid.UUID(str(dto.collection_id)) if dto.collection_id else None,
                    "folder_id": uuid.UUID(str(dto.folder_id)) if dto.folder_id else None,
                    "category_id": uuid.UUID(str(dto.category_id)) if dto.category_id else None,
                    "version": 1,
                    "variables": [
                        PromptVariable(
                            name=var_name,
                            variable_type="string",
                            is_required=True,
                            organization_id=org_uuid,
                        )
                        for var_name in all_vars
                    ],
                    "default_model": dto.default_model,
                    "default_provider": dto.default_provider,
                    "temperature": dto.temperature,
                    "top_p": dto.top_p,
                    "max_tokens": dto.max_tokens,
                    "visibility": dto.visibility,
                    "is_active": True,
                    "is_archived": False,
                }

                prompt = await repo.create(
                    session=self.uow_service.session,
                    obj_in=prompt_data,
                    actor_id=ctx.get_user_id_uuid(),
                )

                self.uow_service.add_event(
                    PromptTemplateCreated(
                        aggregate_id=str(prompt.id),
                        tenant_id=str(org_id),
                        actor_id=ctx.get_user_id_str(),
                        correlation_id=ctx.correlation_id,
                        prompt_id=str(prompt.id),
                        title=dto.title,
                        version=1,
                        payload={"prompt_id": str(prompt.id), "title": dto.title},
                    )
                )

                response = prompt_to_response_dto(prompt)

            await self.cache.delete(org_prompts_list_key(org_id))
            await self.cache.set(prompt_template_cache_key(response.id), response.model_dump(mode="json"), ttl=PROMPT_CACHE_TTL)
            return ServiceResult.ok(data=response, status_code=201)

        except Exception as exc:
            logger.error(f"create_prompt failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def get_prompt(
        self,
        ctx: ServiceContext,
        prompt_id: Union[uuid.UUID, str],
    ) -> ServiceResult[PromptResponseDTO]:
        try:
            cache_key = prompt_template_cache_key(prompt_id)
            cached = await self.cache.get(cache_key)
            if cached is not None:
                return ServiceResult.ok(data=PromptResponseDTO(**cached), metadata={"cached": True})

            async with self.uow_service:
                repo = _PromptRepository()
                prompt = await repo.get_by_id(session=self.uow_service.session, id=prompt_id)
                if not prompt:
                    return ServiceResult.fail(error=f"Prompt '{prompt_id}' not found.", error_code="NOT_FOUND", status_code=404)

                PromptPolicy.can_read(self.authorizer, ctx, org_id=prompt.organization_id)

                response = prompt_to_response_dto(prompt)
                await self.cache.set(cache_key, response.model_dump(mode="json"), ttl=PROMPT_CACHE_TTL)
                return ServiceResult.ok(data=response)

        except Exception as exc:
            logger.error(f"get_prompt failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)

    async def render_prompt(
        self,
        ctx: ServiceContext,
        dto: RenderPromptDTO,
    ) -> ServiceResult[RenderedPromptResponseDTO]:
        try:
            prompt_res = await self.get_prompt(ctx, dto.prompt_id)
            if prompt_res.is_failure:
                return ServiceResult.fail(error=prompt_res.errors[0], error_code=prompt_res.error_code, status_code=prompt_res.status_code)

            prompt = prompt_res.unwrap()
            rendered = prompt.template
            unresolved: List[str] = []

            all_vars = re.findall(PROMPT_VAR_REGEX, prompt.template)
            for var_name in set(all_vars):
                if var_name in dto.variables:
                    val_str = str(dto.variables[var_name])
                    pattern = r"\{\{\s*" + re.escape(var_name) + r"\s*\}\}"
                    rendered = re.sub(pattern, val_str, rendered)
                else:
                    unresolved.append(var_name)

            return ServiceResult.ok(
                data=RenderedPromptResponseDTO(
                    prompt_id=dto.prompt_id,
                    title=prompt.title,
                    rendered_text=rendered,
                    unresolved_variables=unresolved,
                    version=prompt.version,
                )
            )

        except Exception as exc:
            logger.error(f"render_prompt failed: {exc}", exc_info=True)
            return ServiceResult.from_exception(exc)
