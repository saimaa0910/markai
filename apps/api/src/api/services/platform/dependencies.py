"""
EAIMOS Platform Dependencies
=============================
FastAPI dependency providers for Sprint 6 Platform services.
"""

from api.services.base.dependency_provider import container
from api.services.platform.billing_service import BillingService
from api.services.platform.analytics_service import AnalyticsService
from api.services.platform.security_platform_service import SecurityPlatformService


def get_billing_service() -> BillingService:
    return BillingService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_analytics_service() -> AnalyticsService:
    return AnalyticsService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )


def get_security_platform_service() -> SecurityPlatformService:
    return SecurityPlatformService(
        uow_service=container.create_uow_service(),
        cache_manager=container.cache,
        authorizer=container.authorizer,
        dispatcher=container.dispatcher,
    )
