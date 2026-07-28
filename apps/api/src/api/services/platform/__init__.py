"""
EAIMOS Platform Service Layer (Sprint 6)
=========================================
Public API for Billing, Analytics & Security Platform domain services.
"""

from api.services.platform.billing_service import BillingService
from api.services.platform.analytics_service import AnalyticsService
from api.services.platform.security_platform_service import SecurityPlatformService

from api.services.platform.dtos import (
    CreateSubscriptionDTO,
    SubscriptionResponseDTO,
    AddCreditsDTO,
    CreditBalanceResponseDTO,
    AnalyticsQueryDTO,
    AnalyticsSummaryDTO,
    ReportIncidentDTO,
    SecurityIncidentResponseDTO,
)

from api.services.platform.events import (
    SubscriptionCreated,
    CreditsAdded,
    SecurityIncidentReported,
)

from api.services.platform.dependencies import (
    get_billing_service,
    get_analytics_service,
    get_security_platform_service,
)

__all__ = [
    "BillingService",
    "AnalyticsService",
    "SecurityPlatformService",
    "CreateSubscriptionDTO",
    "SubscriptionResponseDTO",
    "AddCreditsDTO",
    "CreditBalanceResponseDTO",
    "AnalyticsQueryDTO",
    "AnalyticsSummaryDTO",
    "ReportIncidentDTO",
    "SecurityIncidentResponseDTO",
    "get_billing_service",
    "get_analytics_service",
    "get_security_platform_service",
]
