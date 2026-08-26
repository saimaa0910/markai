import pytest
import uuid
import time
from sqlalchemy.orm import Session
from api.ai.gateway.coordinator import AIGateway
from api.models.ai_platform import AIProvider
from api.models.ai_registry import AIModelRegistry
from api.core.metrics_registry import (
    ai_provider_circuit_breaker_state,
    ai_provider_circuit_breaker_failures_total,
    ai_provider_circuit_breaker_transitions_total,
)
from api.services.alert_engine import AlertEngine


def test_circuit_breaker_transitions_and_metrics(db_session: Session):
    gateway = AIGateway()
    provider_name = "test_circuit_prov"

    # Verify initial state
    assert gateway._breaker_is_open(provider_name) is None

    # Record consecutive failures until threshold (5)
    for i in range(4):
        gateway._breaker_record_failure(provider_name)
        assert gateway._breaker_is_open(provider_name) is None

    # 5th failure triggers circuit breaker open
    gateway._breaker_record_failure(provider_name, retry_after=30.0)
    remaining = gateway._breaker_is_open(provider_name)
    assert remaining is not None
    assert remaining > 0

    # Check alert engine detection for prolonged open state (>300s)
    alert = AlertEngine.check_prolonged_circuit_breaker_alert(
        db=db_session,
        provider=provider_name,
        open_duration_seconds=350.0,
        threshold_seconds=300.0,
    )
    assert alert is not None
    assert "exceeding the 300s limit" in alert.message

    # Duplicate call should not re-trigger alert for active incident
    alert_duplicate = AlertEngine.check_prolonged_circuit_breaker_alert(
        db=db_session,
        provider=provider_name,
        open_duration_seconds=400.0,
        threshold_seconds=300.0,
    )
    assert alert_duplicate is None

    # Success records reset
    gateway._breaker_record_success(provider_name)
    assert gateway._breaker_is_open(provider_name) is None
