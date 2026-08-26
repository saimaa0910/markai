import os
import logging
from contextlib import contextmanager
from typing import Generator, Optional

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor

logger = logging.getLogger("api.core.telemetry")

# Global tracer variable
tracer = None

def init_telemetry(app=None) -> trace.Tracer:
    """
    Initialize OpenTelemetry SDK with OTLP or Console span processors
    and auto-instrument FastAPI, SQLAlchemy, and Redis.
    """
    global tracer
    
    service_name = os.getenv("OTEL_SERVICE_NAME", "viptant-api")
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    
    resource = Resource.create(attributes={
        "service.name": service_name,
        "environment": os.getenv("ENVIRONMENT", "development")
    })
    
    provider = TracerProvider(resource=resource)
    
    # Configure Span Processor
    if otlp_endpoint:
        try:
            logger.info(f"Configuring OTLP span exporter to {otlp_endpoint}")
            # Use insecure channel or SSL depending on the URL scheme (usually insecure for localhost)
            insecure = otlp_endpoint.startswith("http://")
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=insecure)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        except Exception as e:
            logger.warning(f"Failed to initialize OTLP Span Exporter: {e}. Falling back to Console Span Exporter.")
            provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    else:
        logger.info("No OTLP endpoint configured. Using Console Span Exporter.")
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
        
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer(service_name)
    
    # 1. Instrument SQLAlchemy
    try:
        from api.database.session import engine
        SQLAlchemyInstrumentor().instrument(engine=engine)
        logger.info("SQLAlchemy telemetry instrumentation completed.")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")
        
    # 2. Instrument Redis
    try:
        RedisInstrumentor().instrument()
        logger.info("Redis telemetry instrumentation completed.")
    except Exception as e:
        logger.warning(f"Failed to instrument Redis: {e}")
        
    # 3. Instrument FastAPI
    if app:
        try:
            # We exclude health/liveness endpoints to avoid bloating traces
            FastAPIInstrumentor.instrument_app(
                app, 
                tracer_provider=provider,
                excluded_urls="health,live,ready,metrics"
            )
            logger.info("FastAPI telemetry instrumentation completed.")
        except Exception as e:
            logger.warning(f"Failed to instrument FastAPI: {e}")
            
    return tracer


@contextmanager
def start_span(name: str, attributes: Optional[dict] = None) -> Generator[trace.Span, None, None]:
    """
    Context manager to start a telemetry trace span.
    """
    global tracer
    if tracer is None:
        service_name = os.getenv("OTEL_SERVICE_NAME", "viptant-api")
        tracer = trace.get_tracer(service_name)
        
    with tracer.start_as_current_span(name, attributes=attributes) as span:
        yield span


import contextvars
import uuid

_pseudo_trace_id = contextvars.ContextVar("pseudo_trace_id", default=None)
_pseudo_span_id = contextvars.ContextVar("pseudo_span_id", default=None)


def get_current_trace_and_span_ids() -> tuple[Optional[str], Optional[str]]:
    """
    Helper function to get current trace_id and span_id hex strings.
    Supports a pseudo-trace fallback context if OpenTelemetry is in NoOp/offline mode.
    """
    span_ctx = trace.get_current_span().get_span_context()
    if span_ctx.is_valid:
        trace_id = format(span_ctx.trace_id, '032x')
        span_id = format(span_ctx.span_id, '016x')
        return trace_id, span_id
    
    # ContextVar fallback for self-contained DB tracing/logs (e.g., in unit tests)
    tid = _pseudo_trace_id.get()
    sid = _pseudo_span_id.get()
    if not tid:
        tid = uuid.uuid4().hex
        sid = uuid.uuid4().hex[:16]
        _pseudo_trace_id.set(tid)
        _pseudo_span_id.set(sid)
    return tid, sid


