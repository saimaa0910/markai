"""
EAIMOS Platform Policies
=========================
Authorization policies for Billing, Analytics & Security Platform.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission


class BillingPolicy:
    @staticmethod
    def can_manage(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ORG_WRITE.value)


class AnalyticsPolicy:
    @staticmethod
    def can_view(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.ANALYTICS_READ.value)


class SecurityPlatformPolicy:
    @staticmethod
    def can_manage(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ORG_WRITE.value)
