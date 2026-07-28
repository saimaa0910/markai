"""
Sprint 11 Observability, Telemetry & Incident Monitoring Service Tests
========================================================================
Tests for TelemetryService, LogIngestionService, and IncidentAlertService.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.observability.telemetry_service import TelemetryService
from api.services.observability.log_ingestion_service import LogIngestionService
from api.services.observability.incident_alert_service import IncidentAlertService
from api.services.observability.dtos import (
    RecordTraceDTO,
    IngestLogDTO,
    CreateIncidentDTO,
)


def make_ctx() -> ServiceContext:
    ctx = MagicMock(spec=ServiceContext)
    ctx.user_id = uuid.uuid4()
    ctx.organization_id = uuid.uuid4()
    ctx.correlation_id = str(uuid.uuid4())
    ctx.get_user_id_str.return_value = str(ctx.user_id)
    ctx.get_user_id_uuid.return_value = ctx.user_id
    ctx.get_org_id_str.return_value = str(ctx.organization_id)
    ctx.is_tenant_member.return_value = True
    return ctx


def make_authorizer() -> MagicMock:
    auth = MagicMock()
    auth.require_authenticated.return_value = None
    auth.require_tenant_access.return_value = None
    auth.require_permission.return_value = None
    auth.check_permission.return_value = True
    return auth


def make_uow() -> MagicMock:
    uow = MagicMock()
    uow.__aenter__ = AsyncMock(return_value=uow)
    uow.__aexit__ = AsyncMock(return_value=None)
    uow.session = MagicMock()
    uow.add_event = MagicMock()
    return uow


def make_entity(**kwargs) -> MagicMock:
    entity = MagicMock()
    entity.id = kwargs.get("id", uuid.uuid4())
    entity.created_at = datetime.now(timezone.utc)
    for k, v in kwargs.items():
        setattr(entity, k, v)
    return entity


class TestTelemetryService:
    @pytest.mark.asyncio
    async def test_record_trace(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        now = datetime.now(timezone.utc)
        trace_entity = make_entity(
            trace_id="tr-12345",
            span_id="sp-67890",
            name="POST /api/v1/chat/completions",
            start_time=now,
            end_time=now + timedelta(milliseconds=150),
            duration_ms=150,
            status="success",
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = trace_entity

        svc = TelemetryService(uow_service=uow, cache_manager=cache, authorizer=authorizer)

        with patch("api.services.observability.telemetry_service._AITraceRepository", return_value=repo_mock):
            res = await svc.record_trace(
                ctx,
                dto=RecordTraceDTO(
                    trace_id="tr-12345",
                    span_id="sp-67890",
                    name="POST /api/v1/chat/completions",
                    start_time=now,
                    end_time=now + timedelta(milliseconds=150),
                    status="success",
                ),
            )

        assert res.is_success
        assert res.data.trace_id == "tr-12345"
        assert res.data.duration_ms == 150


class TestLogIngestionService:
    @pytest.mark.asyncio
    async def test_ingest_log(self):
        ctx = make_ctx()

        svc = LogIngestionService()
        res = await svc.ingest_log(
            ctx,
            dto=IngestLogDTO(
                level="INFO",
                logger="api.middleware.logging",
                message="HTTP POST /api/v1/prompts/ resolved 201",
            ),
        )

        assert res.is_success
        assert res.data.level == "INFO"


class TestIncidentAlertService:
    @pytest.mark.asyncio
    async def test_create_incident(self):
        ctx = make_ctx()

        svc = IncidentAlertService()
        res = await svc.create_incident(
            ctx,
            org_id=ctx.organization_id,
            dto=CreateIncidentDTO(
                component="redis",
                service="cache_manager",
                severity="CRITICAL",
                root_cause="Redis connection pool exhausted",
            ),
        )

        assert res.is_success
        assert res.data.component == "redis"
        assert res.data.severity == "CRITICAL"
