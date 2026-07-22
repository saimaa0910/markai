"""
EAIMOS Administration Repository Module — Sprint 15
===================================================
Repository implementations for Administration & Infrastructure models:
SupportTicket, ImpersonationLog, MaintenanceWindow, PlatformAnnouncement, AdminActionLog, AIBackgroundJob.
"""

from typing import Any, List, Optional
import uuid

from api.models.admin import (
    SupportTicket,
    ImpersonationLog,
    MaintenanceWindow,
    PlatformAnnouncement,
    AdminActionLog,
)
from api.models.infrastructure import AIBackgroundJob
from api.repositories.tenant import TenantRepository
from api.repositories.base import BaseRepository
from api.repositories.filters import FilterParam, FilterOperator


class SupportTicketRepository(TenantRepository[SupportTicket]):
    """Data access layer for Customer Support Tickets."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(SupportTicket, organization_id=organization_id)


class ImpersonationLogRepository(BaseRepository[ImpersonationLog]):
    """Data access layer for Admin Impersonation Logs."""

    def __init__(self) -> None:
        super().__init__(ImpersonationLog)


class MaintenanceWindowRepository(BaseRepository[MaintenanceWindow]):
    """Data access layer for Planned Maintenance Windows."""

    def __init__(self) -> None:
        super().__init__(MaintenanceWindow)


class PlatformAnnouncementRepository(BaseRepository[PlatformAnnouncement]):
    """Data access layer for System Announcements."""

    def __init__(self) -> None:
        super().__init__(PlatformAnnouncement)


class AdminActionLogRepository(BaseRepository[AdminActionLog]):
    """Data access layer for System Admin Actions."""

    def __init__(self) -> None:
        super().__init__(AdminActionLog)


class AIBackgroundJobRepository(TenantRepository[AIBackgroundJob]):
    """Data access layer for AI Background Worker Jobs."""

    def __init__(self, organization_id: uuid.UUID) -> None:
        super().__init__(AIBackgroundJob, organization_id=organization_id)
