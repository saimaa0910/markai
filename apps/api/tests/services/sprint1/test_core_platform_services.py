"""
EAIMOS Sprint 1 Core Platform Services Test Suite
=================================================
Pytest test suite verifying OrganizationService, UserService, UserOrganizationService,
SystemConfigService, and AuditLogService.
"""

import asyncio
import uuid
import pytest

from api.repositories.unit_of_work import UnitOfWork
from api.services.base import ServiceContext, UnitOfWorkService
from api.services.core import (
    AuditLogService,
    CreateAuditLogDTO,
    CreateConfigDTO,
    CreateMembershipDTO,
    CreateOrganizationDTO,
    CreateUserDTO,
    OrganizationService,
    SystemConfigService,
    UpdateOrganizationDTO,
    UpdateUserDTO,
    UserOrganizationService,
    UserService,
)


def run_async(coro):
    """Helper to run coroutines in standard pytest functions."""
    return asyncio.run(coro)


def get_test_uow_service(db_session) -> UnitOfWorkService:
    uow = UnitOfWork(session=db_session)
    return UnitOfWorkService(uow=uow)


def test_organization_service_lifecycle(db_session):
    async def _test():
        uow_service = get_test_uow_service(db_session)
        service = OrganizationService(uow_service=uow_service)
        ctx = ServiceContext.create_system_context()

        # 1. Create Organization
        slug = f"acme-{uuid.uuid4().hex[:6]}"
        create_dto = CreateOrganizationDTO(
            name="Acme Corporation",
            slug=slug,
            plan_tier="starter",
            max_members=10,
        )
        res = await service.create(ctx, create_dto)
        assert res.is_success is True
        org = res.unwrap()
        assert org.name == "Acme Corporation"
        assert org.slug == slug

        # 2. Get by Slug
        slug_res = await service.get_by_slug(ctx, slug)
        assert slug_res.is_success is True
        assert slug_res.unwrap().name == "Acme Corporation"

        # 3. Update Tier
        tier_res = await service.update_tier(ctx, org.id, new_tier="enterprise", max_members=50)
        assert tier_res.is_success is True
        assert tier_res.unwrap().plan_tier == "enterprise"

    run_async(_test())


def test_user_service_lifecycle(db_session):
    async def _test():
        uow_service = get_test_uow_service(db_session)
        service = UserService(uow_service=uow_service)
        ctx = ServiceContext.create_system_context()

        # 1. Create User
        email = f"user_{uuid.uuid4().hex[:6]}@example.com"
        create_dto = CreateUserDTO(
            email=email,
            full_name="Alice Smith",
            job_title="Marketing Lead",
        )
        res = await service.create(ctx, create_dto)
        assert res.is_success is True
        user = res.unwrap()
        assert user.full_name == "Alice Smith"

        # 2. Get by Email
        email_res = await service.get_by_email(ctx, email)
        assert email_res.is_success is True
        assert email_res.unwrap().full_name == "Alice Smith"

        # 3. Prevent duplicate email
        dup_res = await service.create(ctx, create_dto)
        assert dup_res.is_failure is True
        assert dup_res.error_code == "EMAIL_ALREADY_EXISTS"

    run_async(_test())


def test_membership_service_lifecycle(db_session):
    async def _test():
        uow_service = get_test_uow_service(db_session)
        org_service = OrganizationService(uow_service=uow_service)
        user_service = UserService(uow_service=uow_service)
        member_service = UserOrganizationService(uow_service=uow_service)
        ctx = ServiceContext.create_system_context()

        # 1. Setup Org & User
        org = (await org_service.create(
            ctx, CreateOrganizationDTO(name="Org Seats", slug=f"seats-{uuid.uuid4().hex[:6]}", max_members=2)
        )).unwrap()

        user1 = (await user_service.create(
            ctx, CreateUserDTO(email=f"u1_{uuid.uuid4().hex[:6]}@test.com", full_name="User One")
        )).unwrap()

        user2 = (await user_service.create(
            ctx, CreateUserDTO(email=f"u2_{uuid.uuid4().hex[:6]}@test.com", full_name="User Two")
        )).unwrap()

        user3 = (await user_service.create(
            ctx, CreateUserDTO(email=f"u3_{uuid.uuid4().hex[:6]}@test.com", full_name="User Three")
        )).unwrap()

        # 2. Add Member 1
        m1_res = await member_service.add_member(
            ctx, CreateMembershipDTO(user_id=user1.id, organization_id=org.id, role="ADMIN")
        )
        assert m1_res.is_success is True

        # 3. Add Member 2
        m2_res = await member_service.add_member(
            ctx, CreateMembershipDTO(user_id=user2.id, organization_id=org.id, role="MEMBER")
        )
        assert m2_res.is_success is True

        # 4. Attempt adding Member 3 (exceeds seat limit of 2)
        m3_res = await member_service.add_member(
            ctx, CreateMembershipDTO(user_id=user3.id, organization_id=org.id, role="GUEST")
        )
        assert m3_res.is_failure is True
        assert m3_res.error_code == "BUSINESS_RULE_VIOLATION"

    run_async(_test())


def test_system_config_service_lifecycle(db_session):
    async def _test():
        uow_service = get_test_uow_service(db_session)
        user_service = UserService(uow_service=uow_service)
        service = SystemConfigService(uow_service=uow_service)

        ctx = ServiceContext.create_system_context()
        user = (await user_service.create(
            ctx, CreateUserDTO(email=f"syscfg_{uuid.uuid4().hex[:6]}@test.com", full_name="Admin User")
        )).unwrap()

        user_ctx = ServiceContext(
            user_id=user.id,
            roles=["super_admin"],
            permissions={"*:*"},
        )

        # 1. Create Config
        key = f"max_ai_prompt_len_{uuid.uuid4().hex[:6]}"
        create_dto = CreateConfigDTO(key=key, value="4096", namespace="ai_gateway")
        res = await service.create(user_ctx, create_dto)
        assert res.is_success is True

        # 2. Get by Key
        key_res = await service.get_by_key(user_ctx, key, namespace="ai_gateway")
        assert key_res.is_success is True
        assert key_res.unwrap().value == "4096"

    run_async(_test())


def test_audit_log_service_lifecycle(db_session):
    async def _test():
        uow_service = get_test_uow_service(db_session)
        org_service = OrganizationService(uow_service=uow_service)
        user_service = UserService(uow_service=uow_service)
        service = AuditLogService(uow_service=uow_service)

        ctx = ServiceContext.create_system_context()

        # Create valid Org & User to satisfy FK constraints
        org = (await org_service.create(
            ctx, CreateOrganizationDTO(name="Audit Org", slug=f"audit-{uuid.uuid4().hex[:6]}")
        )).unwrap()

        user = (await user_service.create(
            ctx, CreateUserDTO(email=f"audit_{uuid.uuid4().hex[:6]}@test.com", full_name="Audit User")
        )).unwrap()

        user_ctx = ServiceContext(
            user_id=user.id,
            organization_id=org.id,
            roles=["system_admin"],
            permissions={"*:*"},
        )

        # 1. Record Audit Log
        res = await service.record_audit_log(
            user_ctx,
            action="USER_LOGIN",
            entity_type="User",
            entity_id=user.id,
            details={"ip": "127.0.0.1"},
        )
        assert res.is_success is True
        log_entry = res.unwrap()
        assert log_entry.action == "USER_LOGIN"

    run_async(_test())
