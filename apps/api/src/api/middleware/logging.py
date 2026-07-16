import time
import uuid
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt

from api.core.config import settings
from api.core.security import ALGORITHM
from api.database.session import SessionLocal
from api.models.observability import AILog
from api.core.telemetry import get_current_trace_and_span_ids

logger = structlog.get_logger("api.middleware.logging")


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log incoming API requests with structured JSON,
    propagate correlation and request IDs, and save request logs to the database.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.perf_counter()
        path = request.url.path
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # 1. Retrieve or generate Correlation ID and Request ID
        correlation_id = request.headers.get("x-correlation-id") or request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = str(uuid.uuid4())

        request_id = request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # 2. Extract Auth Context (Organization ID & User ID) dynamically
        org_id = request.headers.get("x-organization-id") or request.headers.get("X-Organization-ID")
        user_id = None
        
        auth_header = request.headers.get("authorization")
        if auth_header and auth_header.lower().startswith("bearer "):
            token = auth_header.split(" ")[1]
            try:
                payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
                user_id = payload.get("sub")
            except Exception:
                pass

        # 3. Bind context variables to structlog
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            correlation_id=correlation_id,
            request_id=request_id,
            path=path,
            method=method,
            client_ip=client_ip,
        )
        if org_id:
            structlog.contextvars.bind_contextvars(organization_id=org_id)
        if user_id:
            structlog.contextvars.bind_contextvars(user_id=user_id)

        try:
            response = await call_next(request)
            process_time = int((time.perf_counter() - start_time) * 1000)

            # 4. Attach trace identifiers to response headers
            response.headers["x-correlation-id"] = correlation_id
            response.headers["x-request-id"] = request_id

            trace_id, span_id = get_current_trace_and_span_ids()
            if trace_id:
                response.headers["x-trace-id"] = trace_id

            logger.info(
                "Request processed successfully",
                status_code=response.status_code,
                latency_ms=process_time,
            )

            # 5. Write log details to the DB table ai_logs
            # Exclude health and metrics endpoints from DB logs to prevent database bloat
            if not any(skip in path for skip in ["/health", "/ready", "/live", "/metrics"]):
                self._save_log_to_db(
                    trace_id=trace_id,
                    span_id=span_id,
                    correlation_id=correlation_id,
                    request_id=request_id,
                    org_id=org_id,
                    user_id=user_id,
                    level="INFO",
                    message=f"HTTP {method} {path} resolved with status {response.status_code}",
                    payload={
                        "path": path,
                        "method": method,
                        "client_ip": client_ip,
                        "status_code": response.status_code,
                        "latency_ms": process_time,
                    }
                )

            # Reset pseudo trace context variables
            from api.core.telemetry import _pseudo_trace_id, _pseudo_span_id
            _pseudo_trace_id.set(None)
            _pseudo_span_id.set(None)

            return response

        except Exception as e:
            process_time = int((time.perf_counter() - start_time) * 1000)
            logger.error(
                "Request processing raised unhandled exception",
                error=str(e),
                latency_ms=process_time,
            )

            trace_id, span_id = get_current_trace_and_span_ids()
            self._save_log_to_db(
                trace_id=trace_id,
                span_id=span_id,
                correlation_id=correlation_id,
                request_id=request_id,
                org_id=org_id,
                user_id=user_id,
                level="ERROR",
                message=f"HTTP {method} {path} failed: {str(e)}",
                payload={
                    "path": path,
                    "method": method,
                    "client_ip": client_ip,
                    "latency_ms": process_time,
                    "error": str(e),
                }
            )
            # Reset pseudo trace context variables
            from api.core.telemetry import _pseudo_trace_id, _pseudo_span_id
            _pseudo_trace_id.set(None)
            _pseudo_span_id.set(None)

            raise e

    def _save_log_to_db(
        self,
        trace_id: str | None,
        span_id: str | None,
        correlation_id: str,
        request_id: str,
        org_id: str | None,
        user_id: str | None,
        level: str,
        message: str,
        payload: dict
    ) -> None:
        db = SessionLocal()
        try:
            org_uuid = uuid.UUID(org_id) if org_id else None
            user_uuid = uuid.UUID(user_id) if user_id else None
            
            db_log = AILog(
                trace_id=trace_id,
                span_id=span_id,
                correlation_id=correlation_id,
                request_id=request_id,
                organization_id=org_uuid,
                user_id=user_uuid,
                level=level,
                logger="api.middleware.logging",
                message=message,
                payload=payload
            )
            db.add(db_log)
            db.commit()
        except Exception as ex:
            # Fall back to standard logger to avoid recursive errors
            import logging
            logging.getLogger("api.middleware.logging").warning(f"Failed to save log to DB: {ex}")
        finally:
            db.close()
