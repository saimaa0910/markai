import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import structlog

logger = structlog.get_logger("api.core.metrics")


class MetricsTracker:
    """
    Tracks application performance counters.
    In production: routes metrics to Prometheus client registry.
    """
    _request_counter = 0
    _error_counter = 0
    _latency_sum = 0.0

    @classmethod
    def record_request(cls, latency_ms: float, success: bool = True) -> None:
        cls._request_counter += 1
        cls._latency_sum += latency_ms
        if not success:
            cls._error_counter += 1

    @classmethod
    def get_metrics(cls) -> dict:
        avg_latency = (
            cls._latency_sum / cls._request_counter
            if cls._request_counter > 0
            else 0.0
        )
        return {
            "total_requests": cls._request_counter,
            "total_errors": cls._error_counter,
            "avg_latency_ms": round(avg_latency, 2),
        }


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
            latency = (time.perf_counter() - start_time) * 1000
            success = response.status_code < 400
            MetricsTracker.record_request(latency, success)
            return response
        except Exception as exc:
            latency = (time.perf_counter() - start_time) * 1000
            MetricsTracker.record_request(latency, success=False)
            raise exc
