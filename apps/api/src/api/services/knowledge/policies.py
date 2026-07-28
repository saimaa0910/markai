"""
EAIMOS Knowledge Base Policies
===============================
Authorization policies for Knowledge Collections and Vector Search.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission


class KnowledgePolicy:
    @staticmethod
    def can_create_collection(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.KNOWLEDGE_WRITE.value)

    @staticmethod
    def can_read_collection(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.KNOWLEDGE_READ.value)
