"""
EAIMOS Campaign Policies
=========================
Authorization policies for Campaigns, Audiences, and Content Generation.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission


class CampaignPolicy:
    @staticmethod
    def can_create(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value)

    @staticmethod
    def can_read(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_READ.value)

    @staticmethod
    def can_update(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value)

    @staticmethod
    def can_delete(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value)


class AudiencePolicy:
    @staticmethod
    def can_manage(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.MARKETING_CAMPAIGN_WRITE.value)


class ContentGenPolicy:
    @staticmethod
    def can_generate(authorizer: AuthorizationService, ctx: ServiceContext) -> None:
        authorizer.require_authenticated(ctx)
