"""
EAIMOS CRM Policies
====================
Authorization policies for CRM & Sales Pipeline Services.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission


class CRMPolicy:
    @staticmethod
    def can_manage_pipeline(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value)

    @staticmethod
    def can_manage_deals(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value)
