"""
EAIMOS Sprint 0 Base Service Infrastructure Test Suite
======================================================
Pytest unit & integration test suite verifying ServiceContext, ServiceResult, Exception Hierarchy,
Authorization, ValidatorChain, Cache Managers, Domain Events, Event Dispatcher, UnitOfWorkService,
and BaseService lifecycle operations.
"""

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, Optional
import uuid
import pytest
from pydantic import BaseModel
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from api.database.base import Base
from api.repositories.base import BaseRepository
from api.repositories.pagination import OffsetParams
from api.repositories.unit_of_work import UnitOfWork
from api.services.base import (
    AlreadyExistsError,
    AuthorizationService,
    BaseService,
    BusinessRuleViolation,
    DEFAULT_ROLE_PERMISSIONS,
    DomainEvent,
    EnterprisePermission,
    EntityCreated,
    EntityDeleted,
    EntityRestored,
    EntityUpdated,
    EventDispatcher,
    ForbiddenOperation,
    InMemoryCacheManager,
    NotFoundError,
    ServiceContainer,
    ServiceContext,
    ServiceError,
    ServiceResult,
    UnauthorizedOperation,
    UnitOfWorkService,
    ValidationError,
    ValidatorChain,
    validate_business_rule,
    validate_cross_fields,
    validate_required,
)


def run_async(coro):
    """Helper to execute coroutines in test functions."""
    return asyncio.run(coro)


# ── Mock Entity & Repository ──────────────────────────────────────────────────
from sqlalchemy.dialects.postgresql import UUID as PG_UUID

class MockServiceEntity(Base):
    """Isolated mock model for BaseService CRUD testing."""

    __tablename__ = "mock_service_entities"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(PG_UUID(as_uuid=True), nullable=True)


class MockServiceRepository(BaseRepository[MockServiceEntity]):
    """Data access layer for MockServiceEntity."""

    def __init__(self) -> None:
        super().__init__(MockServiceEntity)


class CreateMockEntityDTO(BaseModel):
    name: str
    description: Optional[str] = None


class UpdateMockEntityDTO(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_service_context_helpers():
    ctx = ServiceContext(
        user_id="user_123",
        organization_id="org_456",
        roles=["marketer"],
        permissions={"prompt:read", "knowledge:read"},
        feature_flags={"ai_copilot": True},
    )

    assert ctx.get_user_id_str() == "user_123"
    assert ctx.get_org_id_str() == "org_456"
    assert ctx.has_permission("prompt:read") is True
    assert ctx.has_permission("admin:system") is False
    assert ctx.has_role("marketer") is True
    assert ctx.has_role("super_admin") is False
    assert ctx.has_feature_flag("ai_copilot") is True
    assert ctx.is_tenant_member("org_456") is True
    assert ctx.is_tenant_member("org_999") is False

    system_ctx = ServiceContext.create_system_context()
    assert system_ctx.is_super_admin is True
    assert system_ctx.has_permission("any:permission") is True


def test_service_result_lifecycle():
    ok_res = ServiceResult.ok(data={"key": "value"}, metadata={"meta": 1})
    assert ok_res.is_success is True
    assert ok_res.is_failure is False
    assert bool(ok_res) is True
    assert ok_res.unwrap() == {"key": "value"}

    fail_res = ServiceResult.fail(
        error="Something went wrong",
        error_code="CUSTOM_ERR",
        status_code=400,
    )
    assert fail_res.is_success is False
    assert fail_res.is_failure is True
    assert bool(fail_res) is False

    with pytest.raises(ServiceError) as exc_info:
        fail_res.unwrap()
    assert exc_info.value.error_code == "CUSTOM_ERR"

    exc = ValueError("Native exception")
    res_from_exc = ServiceResult.from_exception(exc)
    assert res_from_exc.is_failure is True
    assert res_from_exc.error_code == "INTERNAL_SERVICE_ERROR"


def test_exception_hierarchy():
    val_err = ValidationError(
        message="Validation failed",
        field_errors=[{"field": "name", "message": "Required"}],
    )
    assert val_err.status_code == 422
    assert val_err.error_code == "VALIDATION_ERROR"
    assert len(val_err.field_errors) == 1

    auth_err = UnauthorizedOperation()
    assert auth_err.status_code == 401

    forb_err = ForbiddenOperation(required_permissions=["admin:system"])
    assert forb_err.status_code == 403

    nf_err = NotFoundError(resource_type="Organization", resource_id="123")
    assert nf_err.status_code == 404


def test_authorization_service():
    auth = AuthorizationService()
    user_ctx = ServiceContext(
        user_id="user_1",
        organization_id="org_1",
        roles=["marketer"],
        permissions={EnterprisePermission.MARKETING_CAMPAIGN_READ.value},
    )

    assert auth.check_authenticated(user_ctx) is True
    assert auth.check_permission(user_ctx, EnterprisePermission.MARKETING_CAMPAIGN_READ.value) is True
    assert auth.check_permission(user_ctx, EnterprisePermission.IAM_USER_DELETE.value) is False
    assert auth.check_tenant_access(user_ctx, "org_1") is True
    assert auth.check_tenant_access(user_ctx, "org_2") is False

    with pytest.raises(ForbiddenOperation):
        auth.require_tenant_access(user_ctx, "org_2")

    assert auth.check_ownership(user_ctx, "user_1") is True
    assert auth.check_ownership(user_ctx, "user_2") is False


def test_validator_chain():
    async def _test():
        chain = ValidatorChain()
        chain.check_required("test_name", "name")
        chain.check_required("", "description")
        chain.check_rule(10 > 5, "GT_CHECK", "Must be greater than 5", "amount")
        chain.check_rule(2 > 5, "GT_FAIL", "Must be greater than 5", "amount")

        assert chain.has_errors is True
        assert len(chain.errors) == 2

        with pytest.raises(ValidationError) as exc_info:
            chain.validate_or_raise()
        assert len(exc_info.value.field_errors) == 2

    run_async(_test())


def test_in_memory_cache_manager():
    async def _test():
        cache = InMemoryCacheManager()
        await cache.set("key1", "val1", ttl=60)
        assert await cache.exists("key1") is True
        assert await cache.get("key1") == "val1"

        await cache.delete("key1")
        assert await cache.get("key1") is None

        await cache.set("org1:item1", "v1")
        await cache.set("org1:item2", "v2")
        await cache.set("org2:item1", "v3")

        deleted = await cache.delete_pattern("org1:*")
        assert deleted == 2
        assert await cache.get("org1:item1") is None
        assert await cache.get("org2:item1") == "v3"

    run_async(_test())


def test_event_dispatcher_and_retry():
    async def _test():
        dispatcher = EventDispatcher(max_retries=2, initial_backoff_sec=0.01)
        received_events = []
        failed_attempts = {"count": 0}

        async def sample_handler(event: DomainEvent):
            received_events.append(event)

        async def flaky_handler(event: DomainEvent):
            failed_attempts["count"] += 1
            if failed_attempts["count"] < 2:
                raise RuntimeError("Flaky error")
            received_events.append(event)

        dispatcher.subscribe(EntityCreated, sample_handler)
        dispatcher.subscribe(EntityCreated, flaky_handler)

        test_event = EntityCreated(
            aggregate_id="123",
            tenant_id="org_1",
            actor_id="user_1",
            entity_name="Organization",
        )

        await dispatcher.publish(test_event)

        assert len(received_events) == 2
        assert len(dispatcher.get_history()) == 1
        assert len(dispatcher.get_dlq()) == 0

    run_async(_test())


def test_event_dispatcher_dlq():
    async def _test():
        dispatcher = EventDispatcher(max_retries=1, initial_backoff_sec=0.01)

        async def broken_handler(event: DomainEvent):
            raise ValueError("Always fails")

        dispatcher.subscribe("broken.event", broken_handler)
        evt = DomainEvent(event_type="broken.event")

        await dispatcher.publish(evt)

        dlq = dispatcher.get_dlq()
        assert len(dlq) == 1
        assert dlq[0]["handler"] == "broken_handler"

    run_async(_test())


def test_unit_of_work_service_transaction_flow():
    async def _test():
        dispatcher = EventDispatcher()
        uow_service = UnitOfWorkService(dispatcher=dispatcher)
        dispatched = []

        async def handler(event: DomainEvent):
            dispatched.append(event)

        dispatcher.subscribe("test.event", handler)

        async with uow_service:
            uow_service.add_event(DomainEvent(event_type="test.event"))
            assert len(dispatched) == 0

        assert len(dispatched) == 1

    run_async(_test())


def test_base_service_crud_lifecycle(db_session):
    async def _test():
        # Create mock table on current test session connection
        MockServiceEntity.__table__.create(bind=db_session.get_bind(), checkfirst=True)

        uow = UnitOfWork(session=db_session)
        dispatcher = EventDispatcher()
        uow_service = UnitOfWorkService(uow=uow, dispatcher=dispatcher)
        cache = InMemoryCacheManager()

        service = BaseService[MockServiceEntity, CreateMockEntityDTO, UpdateMockEntityDTO, MockServiceEntity](
            repository_cls=MockServiceRepository,
            uow_service=uow_service,
            cache_manager=cache,
            dispatcher=dispatcher,
            entity_name="MockServiceEntity",
        )

        ctx = ServiceContext.create_system_context()

        # 1. Create
        create_dto = CreateMockEntityDTO(name="Test Item", description="Service Layer Test")
        create_res = await service.create(ctx, create_dto)
        assert create_res.is_success is True
        created_item = create_res.unwrap()
        assert created_item.name == "Test Item"
        item_id = created_item.id

        # 2. Get By ID
        get_res = await service.get_by_id(ctx, item_id)
        assert get_res.is_success is True
        assert get_res.unwrap().name == "Test Item"

        # 3. Update
        update_dto = UpdateMockEntityDTO(name="Updated Test Item")
        update_res = await service.update(ctx, item_id, update_dto)
        assert update_res.is_success is True
        assert update_res.unwrap().name == "Updated Test Item"

        # 4. Soft Delete
        delete_res = await service.soft_delete(ctx, item_id)
        assert delete_res.is_success is True
        assert delete_res.unwrap().deleted_at is not None

        # 5. Restore
        restore_res = await service.restore(ctx, item_id)
        assert restore_res.is_success is True
        assert restore_res.unwrap().deleted_at is None

        # 6. List
        list_res = await service.list(ctx, OffsetParams(page=1, page_size=10))
        assert list_res.is_success is True
        assert list_res.unwrap().total >= 1

    run_async(_test())
