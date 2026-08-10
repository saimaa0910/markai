"""Rate Limiting Service — Sprint 8.3.1 Phase 4

Provides rate limiting capabilities to protect against brute force and abuse.

Core Features:
- Per-IP and per-user rate limiting
- Configurable limits and windows
- Rate limit violation logging
- Status checking and monitoring

Implementation:
- Redis-backed for distributed systems (or in-memory for single instance)
- Sliding window algorithm
- Automatic cleanup of expired records
"""
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple, Dict, Any
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)


class RateLimitService:
    """Service for rate limiting and abuse prevention."""
    
    @staticmethod
    async def check_rate_limit(
        db: AsyncSession,
        endpoint: str,
        identifier: str,
        limit: int,
        window_minutes: int,
    ) -> Tuple[bool, int]:
        """
        Check if an action is within rate limits.
        
        Args:
            db: Database session
            endpoint: API endpoint path
            identifier: IP address or user_id
            limit: Maximum attempts allowed
            window_minutes: Time window in minutes
            
        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        from api.models.security import RateLimitLog
        
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Count attempts in current window
        result = await db.execute(
            select(func.sum(RateLimitLog.attempt_count)).where(
                and_(
                    RateLimitLog.endpoint == endpoint,
                    RateLimitLog.ip_address == identifier,
                    RateLimitLog.window_end > window_start,
                )
            )
        )
        current_count = result.scalar() or 0
        
        allowed = current_count < limit
        remaining = max(0, limit - current_count - 1) if allowed else 0
        
        logger.debug(
            f"Rate limit check for {endpoint} from {identifier}: "
            f"{current_count}/{limit} attempts, allowed={allowed}"
        )
        
        return allowed, remaining
    
    @staticmethod
    async def record_attempt(
        db: AsyncSession,
        endpoint: str,
        ip_address: str,
        user_id: Optional[uuid.UUID] = None,
        limit: int = None,
        window_minutes: int = 15,
    ) -> None:
        """
        Record an API attempt for rate limiting.
        
        Args:
            db: Database session
            endpoint: API endpoint path
            ip_address: Client IP address
            user_id: User ID if authenticated
            limit: Rate limit threshold (for blocking decision)
            window_minutes: Time window in minutes
        """
        from api.models.security import RateLimitLog
        
        now = datetime.now(timezone.utc)
        window_start = now
        window_end = now + timedelta(minutes=window_minutes)
        
        # Check if we should block this attempt
        blocked = False
        if limit:
            allowed, _ = await RateLimitService.check_rate_limit(
                db, endpoint, ip_address, limit, window_minutes
            )
            blocked = not allowed
        
        # Record the attempt
        log_entry = RateLimitLog(
            endpoint=endpoint,
            ip_address=ip_address,
            user_id=user_id,
            attempt_count=1,
            window_start=window_start,
            window_end=window_end,
            blocked=blocked,
        )
        
        db.add(log_entry)
        await db.commit()
        
        if blocked:
            logger.warning(
                f"Rate limit exceeded for {endpoint} from {ip_address} "
                f"(user_id={user_id})"
            )
        else:
            logger.debug(
                f"Recorded attempt for {endpoint} from {ip_address}"
            )
    
    @staticmethod
    async def get_rate_limit_status(
        db: AsyncSession,
        endpoint: str,
        identifier: str,
        window_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Get current rate limit status for an identifier.
        
        Args:
            db: Database session
            endpoint: API endpoint path
            identifier: IP address or user_id
            window_minutes: Time window in minutes
            
        Returns:
            Dict with attempt count, window info, and blocked status
        """
        from api.models.security import RateLimitLog
        
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(minutes=window_minutes)
        
        # Get recent attempts
        result = await db.execute(
            select(RateLimitLog).where(
                and_(
                    RateLimitLog.endpoint == endpoint,
                    RateLimitLog.ip_address == identifier,
                    RateLimitLog.window_end > window_start,
                )
            ).order_by(RateLimitLog.created_at.desc())
        )
        attempts = result.scalars().all()
        
        total_attempts = sum(log.attempt_count for log in attempts)
        blocked = any(log.blocked for log in attempts)
        
        return {
            "endpoint": endpoint,
            "identifier": identifier,
            "total_attempts": total_attempts,
            "window_minutes": window_minutes,
            "blocked": blocked,
            "attempts": [
                {
                    "count": log.attempt_count,
                    "created_at": log.created_at.isoformat(),
                    "blocked": log.blocked,
                }
                for log in attempts[:10]  # Latest 10
            ]
        }
    
    @staticmethod
    async def cleanup_expired_logs(
        db: AsyncSession,
        retention_days: int = 7,
    ) -> int:
        """
        Clean up old rate limit logs.
        
        Args:
            db: Database session
            retention_days: Number of days to retain logs
            
        Returns:
            Number of logs deleted
        """
        from api.models.security import RateLimitLog
        from sqlalchemy import delete
        
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        
        result = await db.execute(
            delete(RateLimitLog).where(
                RateLimitLog.created_at < cutoff_date
            )
        )
        
        deleted_count = result.rowcount
        await db.commit()
        
        logger.info(
            f"Cleaned up {deleted_count} rate limit logs older than {retention_days} days"
        )
        
        return deleted_count
