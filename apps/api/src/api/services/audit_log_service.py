"""Audit Log Service — Sprint 8.3.1 Phase 3 & Phase 4

Manages comprehensive security event audit logging for compliance and forensics.

Core Features:
- Log security events (login, MFA, device trust, data access)
- Query and filter audit logs
- Track user actions and admin operations
- Support for compliance reporting

Event Types:
- Authentication: login, logout, login_failed, mfa_verified, mfa_failed
- Account: account_created, account_deleted, account_deactivated, account_reactivated
- Data: data_exported, data_deleted
- Device: device_trusted, device_revoked
- MFA: mfa_enabled, mfa_disabled, mfa_recovery_used, mfa_recovery_regenerated
- Rate Limit: rate_limit_exceeded
- Admin: admin_action, suspicious_activity
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class AuditLogService:
    """Service for managing audit logs."""
    
    @staticmethod
    async def log_event(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Log a security or user event.
        
        Args:
            db: Database session
            user_id: User ID who performed the action
            event_type: Type of event (login, logout, etc.)
            ip_address: IP address of the request
            user_agent: User agent string
            details: Additional event-specific details
        """
        from api.models.audit import AuditLog
        
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
        )
        
        db.add(audit_log)
        await db.commit()
        
        logger.info(
            f"Audit event logged: user_id={user_id}, "
            f"event_type={event_type}, ip={ip_address}"
        )
    
    @staticmethod
    async def get_user_logs(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Any]:
        """
        Get audit logs for a specific user.
        
        Args:
            db: Database session
            user_id: User ID to get logs for
            event_type: Optional filter by event type
            from_date: Optional start date filter
            to_date: Optional end date filter
            limit: Maximum number of logs to return
            offset: Offset for pagination
            
        Returns:
            List of audit log records
        """
        from api.models.audit import AuditLog
        
        # Build filter conditions
        conditions = [AuditLog.user_id == user_id]
        
        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        
        if from_date:
            conditions.append(AuditLog.created_at >= from_date)
        
        if to_date:
            conditions.append(AuditLog.created_at <= to_date)
        
        # Execute query
        result = await db.execute(
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        
        logs = result.scalars().all()
        
        logger.debug(
            f"Retrieved {len(logs)} audit logs for user {user_id}"
        )
        
        return logs
    
    @staticmethod
    async def count_user_logs(
        db: AsyncSession,
        user_id: uuid.UUID,
        event_type: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> int:
        """
        Count total audit logs for a user matching filters.
        
        Args:
            db: Database session
            user_id: User ID to count logs for
            event_type: Optional filter by event type
            from_date: Optional start date filter
            to_date: Optional end date filter
            
        Returns:
            Total count of matching logs
        """
        from api.models.audit import AuditLog
        
        # Build filter conditions
        conditions = [AuditLog.user_id == user_id]
        
        if event_type:
            conditions.append(AuditLog.event_type == event_type)
        
        if from_date:
            conditions.append(AuditLog.created_at >= from_date)
        
        if to_date:
            conditions.append(AuditLog.created_at <= to_date)
        
        # Execute count query
        result = await db.execute(
            select(func.count(AuditLog.id)).where(and_(*conditions))
        )
        
        count = result.scalar() or 0
        
        return count
    
    @staticmethod
    async def get_recent_events(
        db: AsyncSession,
        event_types: Optional[List[str]] = None,
        limit: int = 100,
    ) -> List[Any]:
        """
        Get recent audit events across all users.
        
        Args:
            db: Database session
            event_types: Optional list of event types to filter
            limit: Maximum number of events to return
            
        Returns:
            List of recent audit log records
        """
        from api.models.audit import AuditLog
        
        query = select(AuditLog)
        
        if event_types:
            query = query.where(AuditLog.event_type.in_(event_types))
        
        result = await db.execute(
            query.order_by(AuditLog.created_at.desc()).limit(limit)
        )
        
        return result.scalars().all()
    
    @staticmethod
    async def get_suspicious_activity(
        db: AsyncSession,
        from_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Any]:
        """
        Get suspicious security events.
        
        Args:
            db: Database session
            from_date: Optional start date filter
            limit: Maximum number of events to return
            
        Returns:
            List of suspicious audit log records
        """
        from api.models.audit import AuditLog
        
        # Define suspicious event types
        suspicious_events = [
            "login_failed",
            "mfa_failed",
            "rate_limit_exceeded",
            "suspicious_activity",
            "unauthorized_access",
        ]
        
        conditions = [AuditLog.event_type.in_(suspicious_events)]
        
        if from_date:
            conditions.append(AuditLog.created_at >= from_date)
        
        result = await db.execute(
            select(AuditLog)
            .where(and_(*conditions))
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        
        return result.scalars().all()
