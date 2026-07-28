"""
Sprint 12 File Storage, Notifications & Feature Flags Service Tests
====================================================================
Tests for FileStorageService, NotificationService, and FeatureFlagService.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from api.services.base.cache import InMemoryCacheManager
from api.services.base.service_context import ServiceContext
from api.services.base.service_exceptions import ValidationError
from api.services.infrastructure.file_storage_service import FileStorageService
from api.services.infrastructure.notification_service import NotificationService
from api.services.infrastructure.feature_flag_service import FeatureFlagService
from api.services.infrastructure.dtos import (
    UploadFileAssetDTO,
    SendNotificationDTO,
    CreateFeatureFlagDTO,
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


class TestFileStorageService:
    @pytest.mark.asyncio
    async def test_upload_file_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        file_entity = make_entity(
            organization_id=ctx.organization_id,
            filename="test_report.pdf",
            file_type="PDF",
            mime_type="application/pdf",
            file_size=1024,
            storage_url="s3://test/test_report.pdf",
        )

        repo_mock = AsyncMock()
        repo_mock.create.return_value = file_entity

        svc = FileStorageService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )

        with patch(
            "api.services.infrastructure.file_storage_service._FileAssetRepository",
            return_value=repo_mock,
        ):
            res = await svc.upload_file(
                ctx,
                org_id=ctx.organization_id,
                dto=UploadFileAssetDTO(
                    filename="test_report.pdf",
                    file_type="PDF",
                    mime_type="application/pdf",
                    file_size=1024,
                ),
            )

        assert res.is_success
        assert res.data.filename == "test_report.pdf"
        assert res.data.file_size == 1024

    @pytest.mark.asyncio
    async def test_upload_file_size_exceeded(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        svc = FileStorageService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )

        # 60MB (limit is 50MB)
        res = await svc.upload_file(
            ctx,
            org_id=ctx.organization_id,
            dto=UploadFileAssetDTO(
                filename="large_file.zip",
                file_type="ZIP",
                mime_type="application/zip",
                file_size=60 * 1024 * 1024,
            ),
        )

        assert not res.is_success
        assert "exceeds maximum limit" in res.errors[0]


class TestNotificationService:
    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        svc = NotificationService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )

        res = await svc.send_notification(
            ctx,
            dto=SendNotificationDTO(
                recipient="user@example.com",
                channel="EMAIL",
                subject="Test Notification",
                body="Hello World!",
            ),
        )

        assert res.is_success
        assert res.data.recipient == "user@example.com"
        assert res.data.channel == "EMAIL"
        assert res.data.status == "DISPATCHED"

    @pytest.mark.asyncio
    async def test_send_notification_invalid_channel(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        svc = NotificationService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )

        res = await svc.send_notification(
            ctx,
            dto=SendNotificationDTO(
                recipient="user@example.com",
                channel="INVALID_CHANNEL",
                subject="Test Notification",
                body="Hello World!",
            ),
        )

        assert not res.is_success
        assert "Unsupported notification channel" in res.errors[0]


class TestFeatureFlagService:
    @pytest.mark.asyncio
    async def test_create_flag_success(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        flag_entity = make_entity(
            key="new_feature_toggle",
            name="New Feature Toggle",
            is_enabled=True,
            strategy="BOOLEAN",
        )

        repo_mock = AsyncMock()
        repo_mock.get_by_name.return_value = None
        repo_mock.create.return_value = flag_entity

        svc = FeatureFlagService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )

        with patch(
            "api.services.infrastructure.feature_flag_service._FeatureFlagRepository",
            return_value=repo_mock,
        ):
            res = await svc.create_flag(
                ctx,
                org_id=ctx.organization_id,
                dto=CreateFeatureFlagDTO(
                    key="new_feature_toggle",
                    name="New Feature Toggle",
                    is_enabled=True,
                    strategy="BOOLEAN",
                ),
            )

        assert res.is_success
        assert res.data.key == "new_feature_toggle"
        assert res.data.is_enabled is True

    @pytest.mark.asyncio
    async def test_evaluate_flag_cache_hit(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        await cache.set("infrastructure:ff:cached_flag", True)

        svc = FeatureFlagService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )
        res = await svc.evaluate_flag(ctx, flag_key="cached_flag")

        assert res.is_success
        assert res.data is True

    @pytest.mark.asyncio
    async def test_evaluate_flag_cache_miss_db_fetch(self):
        ctx = make_ctx()
        authorizer = make_authorizer()
        cache = InMemoryCacheManager()
        uow = make_uow()

        flag_entity = make_entity(
            name="db_flag",
            display_name="DB Flag",
            is_enabled_globally=True,
        )

        repo_mock = AsyncMock()
        repo_mock.get_by_name.return_value = flag_entity

        svc = FeatureFlagService(
            uow_service=uow, cache_manager=cache, authorizer=authorizer
        )

        with patch(
            "api.services.infrastructure.feature_flag_service._FeatureFlagRepository",
            return_value=repo_mock,
        ):
            res = await svc.evaluate_flag(ctx, flag_key="db_flag")

        assert res.is_success
        assert res.data is True
        # Check cache populate
        assert await cache.get("infrastructure:ff:db_flag") is True
