"""
AI Request Spans & Telemetry Tracer.
"""

from typing import Dict, Any, Optional
from opentelemetry import trace


ai_tracer = trace.get_tracer("eaimos.api.ai")


def trace_llm_call(model: str, prompt: str) -> Any:
    """
    OpenTelemetry span context manager wrapper for LLM requests.
    """
    return ai_tracer.start_as_current_span(f"llm_call.{model}")
