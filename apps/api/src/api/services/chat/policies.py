"""
EAIMOS Chat Policies
====================
Authorization policies for Conversational AI & Real-time Messaging.
"""

import uuid
from typing import Union
from api.services.base.authorization import AuthorizationService
from api.services.base.service_context import ServiceContext


class ChatPolicy:
    @staticmethod
    def can_access(authorizer: AuthorizationService, ctx: ServiceContext, org_id: Union[uuid.UUID, str]) -> None:
        authorizer.require_authenticated(ctx)
        authorizer.require_tenant_access(ctx, org_id)
