"""
EAIMOS Observability Policies
==============================
Authorization policies for Observability, Telemetry & Incidents.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext
from api.services.base.permissions import EnterprisePermission


class ObservabilityPolicy:
    @staticmethod
    def can_view(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
        authorizer.require_permission(ctx, EnterprisePermission.IAM_ORG_READ.value)
