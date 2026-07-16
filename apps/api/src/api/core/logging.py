import logging
import sys
import structlog
from typing import Any, Dict


def inject_telemetry_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processor to inject active OpenTelemetry trace_id and span_id into log events,
    and sanitize any sensitive parameters (PII, API Keys, Passwords).
    """
    # 1. Inject OpenTelemetry Tracing info
    try:
        from api.core.telemetry import get_current_trace_and_span_ids
        trace_id, span_id = get_current_trace_and_span_ids()
        if trace_id:
            event_dict["trace_id"] = trace_id
            event_dict["span_id"] = span_id
    except Exception:
        pass

    # 2. Redact sensitive values from logs
    sensitive_substrings = {"key", "secret", "password", "token", "auth", "credential"}
    for key in list(event_dict.keys()):
        if any(sub in key.lower() for sub in sensitive_substrings):
            val = event_dict[key]
            if isinstance(val, str):
                if len(val) > 8:
                    event_dict[key] = f"{val[:4]}...[REDACTED]...{val[-4:]}"
                else:
                    event_dict[key] = "[REDACTED]"
            else:
                event_dict[key] = "[REDACTED]"

    return event_dict


def setup_logging() -> None:
    """
    Sets up structured logging using structlog.
    Configures formatters, processors, and handlers.
    """
    # Configure stdlib logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            inject_telemetry_context,
            # JSON format suitable for production observability (Datadog/Elastic/Grafana Loki)
            structlog.processors.JSONRenderer(),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
