"""Rate Limiting Middleware — Sprint 8.3.1 Phase 4

Middleware for enforcing rate limits on API endpoints.
"""
import logging
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from api.core.database import async_session_maker
from api.services.rate_limit_service import RateLimitService


logger = logging.getLogger(__name__)


# Rate limit configurations for different endpoints.
# Paths verified against the registered routers (Phase 13).
RATE_LIMIT_CONFIG = {
    "/api/v1/auth/login": {"limit": 5, "window_minutes": 15},
    "/api/v1/auth/register": {"limit": 3, "window_minutes": 60},
    "/api/v1/auth/forgot-password": {"limit": 3, "window_minutes": 60},
    "/api/v1/auth/reset-password": {"limit": 5, "window_minutes": 15},
    "/api/v1/auth/mfa/login": {"limit": 5, "window_minutes": 15},
    "/api/v1/auth/resend-verification": {"limit": 3, "window_minutes": 60},
    "/api/v1/auth/account/restore": {"limit": 5, "window_minutes": 15},
    "/api/v1/auth/account/delete": {"limit": 5, "window_minutes": 15},
}

# P2-12: default rate limit applied to all other /api/v1 endpoints.
DEFAULT_RATE_LIMIT_CONFIG = {"limit": 300, "window_minutes": 1}
# Endpoints exempt from the default general limit (health/status endpoints).
GENERAL_EXEMPT_PREFIXES = (
    "/api/v1/health",
    "/api/v1/status",
    "/api/v1/metrics",
    "/metrics",
    "/api/v1/ai/providers/health",
    "/api/v1/ai/providers/health-logs",
)

AI_RATE_LIMIT_ENDPOINTS = (
    "/api/v1/ai/chat",
    "/api/v1/ai/stream",
    "/api/v1/ai/playground/chat",
    "/api/v1/ai/playground/stream",
    "/api/v1/ai/embeddings",
)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on specified auth & AI endpoints."""
    
    def __init__(self, app, exempt_ips: Optional[list] = None):
        super().__init__(app)
        self.exempt_ips = exempt_ips or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if IP is exempt
        if client_ip in self.exempt_ips:
            return await call_next(request)
        
        # Get endpoint path
        path = request.url.path

        # 1. Exempt health and diagnostic check endpoints
        if path.startswith(GENERAL_EXEMPT_PREFIXES) or "/health-check" in path:
            return await call_next(request)

        # 2. AI Platform Endpoint Rate Limiting (P3-2)
        if any(path.startswith(ep) for ep in AI_RATE_LIMIT_ENDPOINTS):
            org_id_header = request.headers.get("X-Organization-ID")
            ai_identifier = f"ai_org:{org_id_header}" if org_id_header else f"ai_ip:{client_ip}"
            
            # Default AI limits (RPM: 60 per minute per organization or IP)
            ai_rpm_limit = 60
            ai_window_seconds = 60

            async with async_session_maker() as db:
                try:
                    # Query custom org limit if organization header is provided
                    if org_id_header:
                        try:
                            from sqlalchemy import select
                            from api.models.ai_platform import AIOrgLimit
                            import uuid as _uuid
                            
                            org_uuid = _uuid.UUID(org_id_header)
                            res = await db.execute(select(AIOrgLimit).where(AIOrgLimit.organization_id == org_uuid))
                            org_limit_rec = res.scalars().first()
                            if org_limit_rec and org_limit_rec.rpm_limit:
                                ai_rpm_limit = org_limit_rec.rpm_limit
                        except Exception:
                            pass

                    allowed = await RateLimitService.check_rate_limit(
                        db=db,
                        endpoint=path,
                        identifier=ai_identifier,
                        max_attempts=ai_rpm_limit,
                        window_seconds=ai_window_seconds,
                    )

                    if not allowed:
                        logger.warning(f"AI Rate limit exceeded for {path} by {ai_identifier} (Limit: {ai_rpm_limit}/min)")
                        try:
                            from api.core.metrics_registry import ai_request_error_class_total
                            ai_request_error_class_total.labels(provider="gateway", error_type="rate_limited_429").inc()
                        except Exception:
                            pass

                        await RateLimitService.record_attempt(
                            db=db,
                            endpoint=path,
                            ip_address=client_ip,
                            user_id=None,
                            max_attempts=ai_rpm_limit,
                            window_seconds=ai_window_seconds,
                        )

                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={
                                "detail": f"AI Rate limit exceeded ({ai_rpm_limit} requests/min). Please slow down.",
                                "retry_after": ai_window_seconds,
                            },
                            headers={
                                "X-RateLimit-Limit": str(ai_rpm_limit),
                                "X-RateLimit-Remaining": "0",
                                "X-RateLimit-Reset": str(ai_window_seconds),
                                "Retry-After": str(ai_window_seconds),
                            },
                        )

                    await RateLimitService.record_attempt(
                        db=db,
                        endpoint=path,
                        ip_address=client_ip,
                        user_id=None,
                    )

                    response = await call_next(request)
                    response.headers["X-RateLimit-Limit"] = str(ai_rpm_limit)
                    response.headers["X-RateLimit-Remaining"] = "1"
                    response.headers["X-RateLimit-Reset"] = str(ai_window_seconds)
                    return response
                except Exception as e:
                    logger.error(f"Error checking AI rate limit: {e}", exc_info=True)
                    return await call_next(request)

        # 3. Standard Auth & General Endpoint Rate Limiting
        config = RATE_LIMIT_CONFIG.get(path)
        if config is None:
            if path.startswith("/api/v1"):
                config = DEFAULT_RATE_LIMIT_CONFIG

        if config:
            limit = config["limit"]
            window_seconds = config["window_minutes"] * 60

            async with async_session_maker() as db:
                try:
                    allowed = await RateLimitService.check_rate_limit(
                        db=db,
                        endpoint=path,
                        identifier=client_ip,
                        max_attempts=limit,
                        window_seconds=window_seconds,
                    )

                    if not allowed:
                        logger.warning(f"Rate limit exceeded for {path} from {client_ip}")

                        await RateLimitService.record_attempt(
                            db=db,
                            endpoint=path,
                            ip_address=client_ip,
                            user_id=None,
                            max_attempts=limit,
                            window_seconds=window_seconds,
                        )

                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={
                                "detail": "Rate limit exceeded. Please try again later.",
                                "retry_after_seconds": window_seconds,
                            },
                            headers={
                                "X-RateLimit-Limit": str(limit),
                                "X-RateLimit-Remaining": "0",
                                "X-RateLimit-Reset": str(window_seconds),
                                "Retry-After": str(window_seconds),
                            },
                        )

                    await RateLimitService.record_attempt(
                        db=db,
                        endpoint=path,
                        ip_address=client_ip,
                        user_id=None,
                    )

                    response = await call_next(request)
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Remaining"] = "1" if allowed else "0"
                    response.headers["X-RateLimit-Reset"] = str(window_seconds)
                    return response
                    
                except Exception as e:
                    logger.error(f"Error checking rate limit: {e}", exc_info=True)
                    return await call_next(request)
        
        return await call_next(request)


def get_rate_limit_middleware(exempt_ips: Optional[list] = None):
    """
    Factory function to create rate limit middleware.
    
    Args:
        exempt_ips: List of IP addresses exempt from rate limiting
        
    Returns:
        Configured middleware instance
    """
    def middleware(app):
        return RateLimitMiddleware(app, exempt_ips=exempt_ips)
    
    return middleware
