"""
EAIMOS Analytics Repository Module — Sprint 13
==============================================
Repository implementations for Analytics models:
AnalyticsSnapshot, AnalyticsDashboard, AnalyticsWidget, AnalyticsReport, AnalyticsEvent.
"""

from typing import Any, List, Optional
import uuid

from api.models.analytics import (
    AnalyticsSnapshot,
    AnalyticsDashboard,
    AnalyticsWidget,
    AnalyticsReport,
    AnalyticsEvent,
)
from api.repositories.tenant import TenantRepository
from api.repositories.filters import FilterParam, FilterOperator


class AnalyticsDashboardRepository(TenantRepository[AnalyticsDashboard]):
    """Data access layer for Custom Analytics Dashboards."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AnalyticsDashboard, organization_id=organization_id)


class AnalyticsWidgetRepository(TenantRepository[AnalyticsWidget]):
    """Data access layer for Dashboard Widgets."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AnalyticsWidget, organization_id=organization_id)


class AnalyticsReportRepository(TenantRepository[AnalyticsReport]):
    """Data access layer for Custom Analytics Reports."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AnalyticsReport, organization_id=organization_id)


class AnalyticsEventRepository(TenantRepository[AnalyticsEvent]):
    """Data access layer for Product Analytics Events."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AnalyticsEvent, organization_id=organization_id)


class AnalyticsSnapshotRepository(TenantRepository[AnalyticsSnapshot]):
    """Data access layer for Periodic Analytics Snapshots."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AnalyticsSnapshot, organization_id=organization_id)
