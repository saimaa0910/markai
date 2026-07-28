"""
EAIMOS AI Gateway Policies
============================
Authorization policies for prompt engineering, router configs, RAG search, and usage.
"""

import uuid
from typing import Union, Optional
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission
from api.services.base.service_exceptions import ForbiddenOperation


class PromptPolicy:
    @staticmethod
    def can_create(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.PROMPT_CREATE.value)

    @staticmethod
    def can_read(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.PROMPT_READ.value)

    @staticmethod
    def can_update(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.PROMPT_UPDATE.value)

    @staticmethod
    def can_delete(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.PROMPT_DELETE.value)


class RouterPolicy:
    @staticmethod
    def can_route(authorizer: AuthorizationService, ctx: ServiceContext) -> None:
        authorizer.require_authenticated(ctx)


class RAGPolicy:
    @staticmethod
    def can_index(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.KNOWLEDGE_WRITE.value)

    @staticmethod
    def can_search(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.KNOWLEDGE_READ.value)


class MemoryPolicy:
    @staticmethod
    def can_access(authorizer: AuthorizationService, ctx: ServiceContext) -> None:
        authorizer.require_authenticated(ctx)


class AIUsagePolicy:
    @staticmethod
    def can_view(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.ANALYTICS_READ.value)
