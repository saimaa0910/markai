import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger("api.middleware.logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log incoming API requests, HTTP status codes,
    execution latency, client IP address, and method traces.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # Inject context information
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            path=path,
            method=method,
            client_ip=client_ip,
        )

        try:
            response = await call_next(request)
            process_time = int((time.perf_counter() - start_time) * 1000)

            logger.info(
                "Request processed successfully",
                status_code=response.status_code,
                latency_ms=process_time,
            )
            return response

        except Exception as e:
            process_time = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                "Request processing raised unhandled exception",
                error=str(e),
                latency_ms=process_time,
            )
            raise e
