"""
Pytest Test Suite — Sprint 1: Core Platform Repository Layer
============================================================
Comprehensive test coverage for:
- CRUD & Bulk Operations
- Multi-Tenant Isolation
- Pagination (Offset & Cursor)
- Dynamic Filtering & Sorting
- Soft Delete & Restore
- Optimistic Locking
- Unit of Work & Transactions
- Error Handling
"""

import asyncio
import uuid
import pytest
from api.models import Organization, User, UserOrganization, SystemConfiguration, AuditLog
from api.repositories import (
    BaseRepository,
    TenantRepository,
    OrganizationRepository,
    UserRepository,
    UserOrganizationRepository,
    SystemConfigRepository,
    AuditLogRepository,
    SearchRepository,
    UnitOfWork,
    OffsetParams,
    CursorParams,
    FilterParam,
    FilterOperator,
    SortParam,
    SortDirection,
    OptimisticLockError,
    TenantViolationError,
    EntityNotFoundError,
)


def run_async(coro):
    """Helper to run async coroutines in standard pytest functions."""
    return asyncio.run(coro)


def test_organization_repository_crud(db_session):
    async def _test():
        repo = OrganizationRepository()

        # 1. Create
        org_data = {
            "name": "Acme Corp",
            "slug": f"acme-{uuid.uuid4().hex[:6]}",
            "plan_tier": "enterprise",
        }
        org = await repo.create(db_session, org_data, actor_id="user_admin_1")
        assert org.id is not None
        assert org.name == "Acme Corp"
        assert org.created_by == "user_admin_1"
        assert org.version == 1

        # 2. Get by ID & Slug
        fetched = await repo.get_by_id(db_session, org.id)
        assert fetched is not None
        assert fetched.id == org.id

        fetched_slug = await repo.get_by_slug(db_session, org.slug)
        assert fetched_slug is not None
        assert fetched_slug.id == org.id

        # 3. Update
        updated = await repo.update(db_session, org.id, {"name": "Acme Global"}, actor_id="user_admin_2")
        assert updated.name == "Acme Global"
        assert updated.updated_by == "user_admin_2"
        assert updated.version == 2

        # 4. Soft Delete
        deleted = await repo.soft_delete(db_session, org.id)
        assert deleted.deleted_at is not None

        # Verify excluded by default
        active = await repo.get_by_id(db_session, org.id)
        assert active is None

        # Verify retrieved with include_deleted=True
        with_deleted = await repo.get_by_id(db_session, org.id, include_deleted=True)
        assert with_deleted is not None

        # 5. Restore
        restored = await repo.restore(db_session, org.id)
        assert restored.deleted_at is None

    run_async(_test())


def test_tenant_repository_isolation(db_session):
    async def _test():
        org_repo = OrganizationRepository()
        user_repo = UserRepository()

        org1 = await org_repo.create(db_session, {"name": "Org 1", "slug": f"org1-{uuid.uuid4().hex[:6]}"})
        org2 = await org_repo.create(db_session, {"name": "Org 2", "slug": f"org2-{uuid.uuid4().hex[:6]}"})

        user1 = await user_repo.create(db_session, {
            "email": f"user1-{uuid.uuid4().hex[:6]}@example.com",
            "hashed_password": "secret_pw_hash",
            "full_name": "User One",
            "first_name": "User",
            "last_name": "One",
        })
        user2 = await user_repo.create(db_session, {
            "email": f"user2-{uuid.uuid4().hex[:6]}@example.com",
            "hashed_password": "secret_pw_hash",
            "full_name": "User Two",
            "first_name": "User",
            "last_name": "Two",
        })

        repo_org1 = UserOrganizationRepository(organization_id=org1.id)
        repo_org2 = UserOrganizationRepository(organization_id=org2.id)

        # Create under Org 1
        m1 = await repo_org1.create(db_session, {"user_id": user1.id, "role": "admin"})
        assert m1.organization_id == org1.id

        # Create under Org 2
        m2 = await repo_org2.create(db_session, {"user_id": user2.id, "role": "member"})
        assert m2.organization_id == org2.id

        # Org 1 repo must NOT see Org 2 data
        org1_members = await repo_org1.find_many(db_session)
        assert len(org1_members) == 1
        assert org1_members[0].id == m1.id

        # Cross-tenant access attempt should be prevented
        cross_access = await repo_org1.get_by_id(db_session, m2.id)
        assert cross_access is None

        with pytest.raises(TenantViolationError):
            await repo_org1.update(db_session, m2.id, {"role": "owner"})

    run_async(_test())


def test_optimistic_locking(db_session):
    async def _test():
        repo = OrganizationRepository()
        org = await repo.create(db_session, {"name": "TechCorp", "slug": f"tech-{uuid.uuid4().hex[:6]}"})

        assert org.version == 1

        # First update passes with version 1
        await repo.update(db_session, org.id, {"name": "TechCorp 2"}, expected_version=1)

        # Next update with stale version 1 MUST fail
        with pytest.raises(OptimisticLockError):
            await repo.update(db_session, org.id, {"name": "TechCorp Stale"}, expected_version=1)

    run_async(_test())


def test_pagination_and_filtering(db_session):
    async def _test():
        repo = UserRepository()

        # Seed users
        for i in range(15):
            await repo.create(
                db_session,
                {
                    "email": f"user_{i}_{uuid.uuid4().hex[:4]}@example.com",
                    "hashed_password": "hashed_password_secret",
                    "full_name": f"User {i}",
                    "first_name": f"User{i}",
                    "last_name": "Test",
                    "is_active": i % 2 == 0,
                },
            )

        # Offset Pagination
        params = OffsetParams(page=1, page_size=5)
        page_res = await repo.paginated_query(db_session, params=params)
        assert len(page_res.items) == 5
        assert page_res.total >= 15
        assert page_res.has_next is True

        # Filter by is_active = True
        filters = [FilterParam(field="is_active", operator=FilterOperator.EQ, value=True)]
        active_res = await repo.paginated_query(db_session, params=params, filters=filters)
        assert all(u.is_active is True for u in active_res.items)

        # Cursor Pagination
        cursor_params = CursorParams(limit=5, sort_field="created_at", sort_order="desc")
        cursor_res = await repo.cursor_paginated_query(db_session, params=cursor_params)
        assert len(cursor_res.items) == 5
        assert cursor_res.next_cursor is not None

        # Next page via cursor
        cursor_params2 = CursorParams(cursor=cursor_res.next_cursor, limit=5, sort_field="created_at", sort_order="desc")
        cursor_res2 = await repo.cursor_paginated_query(db_session, params=cursor_params2)
        assert len(cursor_res2.items) == 5
        assert cursor_res2.items[0].id != cursor_res.items[0].id

    run_async(_test())


def test_unit_of_work_transaction_rollback(db_session):
    async def _test():
        repo = OrganizationRepository()

        try:
            async with UnitOfWork(session=db_session) as uow:
                org = await repo.create(uow.session, {"name": "Rollback Inc", "slug": f"rollback-{uuid.uuid4().hex[:6]}"})
                assert org.id is not None
                # Force intentional exception to trigger rollback
                raise RuntimeError("Simulated failure during transaction")
        except RuntimeError:
            pass

        # Verify entity was NOT saved due to rollback
        filters = [FilterParam(field="name", operator=FilterOperator.EQ, value="Rollback Inc")]
        found = await repo.find_one(db_session, filters=filters)
        assert found is None

    run_async(_test())


def test_search_repository(db_session):
    async def _test():
        search_repo = SearchRepository(Organization, search_columns=["name", "slug"])

        slug1 = f"search-alpha-{uuid.uuid4().hex[:6]}"
        slug2 = f"search-beta-{uuid.uuid4().hex[:6]}"

        await search_repo.create(db_session, {"name": "Alpha Innovations", "slug": slug1})
        await search_repo.create(db_session, {"name": "Beta Solutions", "slug": slug2})

        results, total = await search_repo.search(db_session, search_query="Alpha")
        assert total >= 1
        assert any(r.slug == slug1 for r in results)

    run_async(_test())
