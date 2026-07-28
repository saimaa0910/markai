"""
EAIMOS Core Platform Dependency Providers
==========================================
FastAPI dependency injection factories for Core Platform services.
"""

from api.services.base.dependency_provider import container
from api.services.core.organization_service import OrganizationService
from api.services.core.user_service import UserService
from api.services.core.membership_service import UserOrganizationService
from api.services.core.system_config_service import SystemConfigService
from api.services.core.audit_log_service import AuditLogService


def get_organization_service() -> OrganizationService:
    return OrganizationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_user_service() -> UserService:
    return UserService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_user_organization_service() -> UserOrganizationService:
    return UserOrganizationService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
