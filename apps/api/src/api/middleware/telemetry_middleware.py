import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from opentelemetry import trace

from api.core.metrics_registry import ai_requests_total, ai_request_latency_seconds, ai_errors_total

class TelemetryMiddleware(BaseHTTPMiddleware):
    """
    Middleware to intercept FastAPI requests, extract trace/span information,
    and report request performance metrics to the Prometheus registry.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        method = request.method
        
        # Skip instrumentation on telemetry endpoints to avoid feedback loops
        if any(skip in path for skip in ["/health", "/ready", "/live", "/metrics"]):
            return await call_next(request)

        # Extract context tags
        org_id = request.headers.get("x-organization-id") or request.headers.get("X-Organization-ID") or "system"
        
        # Resolve active OpenTelemetry span
        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            span.set_attribute("http.method", method)
            span.set_attribute("http.route", path)
            span.set_attribute("organization.id", org_id)

        start_time = time.perf_counter()
        
        try:
            response = await call_next(request)
            duration = time.perf_counter() - start_time
            
            status_code = str(response.status_code)
            
            # Extract provider & model if this was an AI request (e.g. from response headers, or default)
            provider = response.headers.get("x-ai-provider", "gateway")
            model = response.headers.get("x-ai-model", "router")
            
            # Record Prometheus Metrics
            ai_requests_total.labels(
                organization_id=org_id,
                provider=provider,
                model=model,
                status="success" if response.status_code < 400 else "error"
            ).inc()
            
            ai_request_latency_seconds.labels(
                organization_id=org_id,
                provider=provider,
                model=model,
                layer="gateway"
            ).observe(duration)
            
            if response.status_code >= 400:
                ai_errors_total.labels(
                    organization_id=org_id,
                    provider=provider,
                    model=model,
                    error_code=status_code,
                    layer="gateway"
                ).inc()

            return response
            
        except Exception as e:
            duration = time.perf_counter() - start_time
            
            ai_requests_total.labels(
                organization_id=org_id,
                provider="gateway",
                model="router",
                status="error"
            ).inc()
            
            ai_request_latency_seconds.labels(
                organization_id=org_id,
                provider="gateway",
                model="router",
                layer="gateway"
            ).observe(duration)
            
            ai_errors_total.labels(
                organization_id=org_id,
                provider="gateway",
                model="router",
                error_code="500",
                layer="gateway"
            ).inc()
            
            raise e
