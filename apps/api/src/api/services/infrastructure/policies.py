"""
EAIMOS Infrastructure Policies
===============================
Authorization policies for File Storage, Notifications & Feature Flags.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission


class InfrastructurePolicy:
    @staticmethod
    def can_upload_files(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)

    @staticmethod
    def can_manage_notifications(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.NOTIFICATION_SEND.value)

    @staticmethod
    def can_manage_feature_flags(
        authorizer: AuthorizationService,
        ctx: ServiceContext,
        org_id: Union[uuid.UUID, str],
    ) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        # Only admins or super admins can manage feature flags
        authorizer.require_permission(ctx, EnterprisePermission.ADMIN_SYSTEM.value)
