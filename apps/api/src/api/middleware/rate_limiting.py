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


# Rate limit configurations for different endpoints
RATE_LIMIT_CONFIG = {
    "/api/v1/auth/login": {"limit": 5, "window_minutes": 15},
    "/api/v1/auth/register": {"limit": 3, "window_minutes": 60},
    "/api/v1/auth/password-reset/request": {"limit": 3, "window_minutes": 60},
    "/api/v1/auth/mfa/verify": {"limit": 5, "window_minutes": 15},
    "/api/v1/auth/email-verification/request": {"limit": 3, "window_minutes": 60},
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware to enforce rate limits on specified endpoints."""
    
    def __init__(self, app, exempt_ips: Optional[list] = None):
        """
        Initialize rate limiting middleware.
        
        Args:
            app: FastAPI application
            exempt_ips: List of IP addresses exempt from rate limiting
        """
        super().__init__(app)
        self.exempt_ips = exempt_ips or []
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and enforce rate limits.
        """
        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        
        # Check if IP is exempt
        if client_ip in self.exempt_ips:
            return await call_next(request)
        
        # Get endpoint path
        path = request.url.path
        
        # Check if this endpoint has rate limiting configured
        if path in RATE_LIMIT_CONFIG:
            config = RATE_LIMIT_CONFIG[path]
            limit = config["limit"]
            window_minutes = config["window_minutes"]
            
            # Check rate limit using database
            async with async_session_maker() as db:
                try:
                    allowed, remaining = await RateLimitService.check_rate_limit(
                        db=db,
                        endpoint=path,
                        identifier=client_ip,
                        limit=limit,
                        window_minutes=window_minutes,
                    )
                    
                    if not allowed:
                        logger.warning(
                            f"Rate limit exceeded for {path} from {client_ip}"
                        )
                        
                        # Record the blocked attempt
                        await RateLimitService.record_attempt(
                            db=db,
                            endpoint=path,
                            ip_address=client_ip,
                            user_id=None,
                            limit=limit,
                            window_minutes=window_minutes,
                        )
                        
                        return JSONResponse(
                            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                            content={
                                "detail": "Rate limit exceeded. Please try again later.",
                                "retry_after_seconds": window_minutes * 60,
                            },
                            headers={
                                "X-RateLimit-Limit": str(limit),
                                "X-RateLimit-Remaining": "0",
                                "X-RateLimit-Reset": str(window_minutes * 60),
                                "Retry-After": str(window_minutes * 60),
                            },
                        )
                    
                    # Record successful attempt
                    await RateLimitService.record_attempt(
                        db=db,
                        endpoint=path,
                        ip_address=client_ip,
                        user_id=None,
                    )
                    
                    # Add rate limit headers to response
                    response = await call_next(request)
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Remaining"] = str(remaining)
                    response.headers["X-RateLimit-Reset"] = str(window_minutes * 60)
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Error checking rate limit: {e}", exc_info=True)
                    # On error, allow the request (fail open)
                    return await call_next(request)
        
        # No rate limiting for this endpoint
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
