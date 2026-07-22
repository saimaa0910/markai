"""
EAIMOS Audit Repository & Metadata Utilities
============================================
Handles automatic population and auditing of entity audit fields:
created_by, updated_by, deleted_at, version.
"""

from typing import Any, Dict, Optional
import uuid
from sqlalchemy import select
from api.models.auth import AuditLog
from api.repositories.base import BaseRepository
from api.repositories.interfaces import IAuditRepository


class AuditRepository(BaseRepository[AuditLog], IAuditRepository):
    """Repository for recording and searching System & Security Audit Logs."""

    def __init__(self) -> None:
        super().__init__(AuditLog)

    async def log_event(
        self,
        session: Any,
        event_type: str,
        actor_id: Optional[str],
        organization_id: Optional[uuid.UUID],
        resource_type: str,
        resource_id: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """Create a new immutable audit log entry."""
        log_entry = AuditLog(
            action=event_type,
            user_id=actor_id,
            organization_id=organization_id,
            resource=f"{resource_type}:{resource_id}",
            details=payload or {},
        )
        session.add(log_entry)
        await self._flush(session)
        return log_entry
