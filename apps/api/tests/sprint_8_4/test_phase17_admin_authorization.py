"""Sprint 8.4 Phase 17: Admin Authorization Tests

Acceptance criteria: users CRUD endpoints enforce backend authorization so a
regular (or guest) member cannot enumerate, modify, or delete arbitrary users.

Covers:
- Non-superuser listing is scoped to shared organizations (no global leak).
- Non-superuser cannot PATCH / DELETE another user (403).
- Superuser can list, update, and delete users.
- Admin update rejects privilege-escalation fields (email / is_superuser).
"""
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.security import create_access_token, get_password_hash
from api.models.membership import UserOrganization, UserRole
from api.models.organization import Organization
from api.models.user import User


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


async def _user(db: AsyncSession, *, superuser: bool = False) -> User:
    user = User(
        email=f"phase17_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Phase 17 User",
        is_active=True,
        is_verified=True,
        is_superuser=superuser,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _headers(user: User, session_id: uuid.UUID | None = None) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, token_id=session_id)}"}


class TestListUsers:
    @pytest.mark.asyncio
    async def test_list_is_scoped_for_regular_user(self, client, db):
        org = Organization(name="Shared Org", slug=f"p17-org-{uuid.uuid4().hex[:8]}")
        db.add(org)
        await db.flush()

        member_a = await _user(db)
        member_b = await _user(db)
        outsider = await _user(db)

        db.add(UserOrganization(user_id=member_a.id, organization_id=org.id, role=UserRole.MEMBER))
        db.add(UserOrganization(user_id=member_b.id, organization_id=org.id, role=UserRole.MEMBER))
        await db.commit()

        response = client.get("/api/v1/users/", headers=_headers(member_a))
        assert response.status_code == 200
        emails = {u["email"] for u in response.json()}
        assert member_a.email in emails
        assert member_b.email in emails
        assert outsider.email not in emails

    @pytest.mark.asyncio
    async def test_superuser_lists_everyone(self, client, db):
        admin = await _user(db, superuser=True)
        other = await _user(db)

        response = client.get("/api/v1/users/", headers=_headers(admin))
        assert response.status_code == 200
        emails = {u["email"] for u in response.json()}
        assert admin.email in emails
        assert other.email in emails


class TestUpdateUser:
    @pytest.mark.asyncio
    async def test_regular_user_cannot_update_others(self, client, db):
        actor = await _user(db)
        victim = await _user(db)

        response = client.patch(
            f"/api/v1/users/{victim.id}",
            headers=_headers(actor),
            json={"full_name": "Hacked Name"},
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_update_user(self, client, db):
        admin = await _user(db, superuser=True)
        victim = await _user(db)

        response = client.patch(
            f"/api/v1/users/{victim.id}",
            headers=_headers(admin),
            json={"full_name": "Renamed"},
        )
        assert response.status_code == 200
        assert response.json()["full_name"] == "Renamed"

    @pytest.mark.asyncio
    async def test_admin_cannot_escalate_privileges(self, client, db):
        admin = await _user(db, superuser=True)
        victim = await _user(db)

        # email is a real updatable schema field and must be rejected outright.
        response = client.patch(
            f"/api/v1/users/{victim.id}",
            headers=_headers(admin),
            json={"email": "steal@example.com"},
        )
        assert response.status_code == 403

        # is_superuser is not a permitted schema field; it must never be applied.
        response = client.patch(
            f"/api/v1/users/{victim.id}",
            headers=_headers(admin),
            json={"is_superuser": True},
        )
        assert response.status_code in (200, 403)
        fresh = (
            await db.execute(
                select(User).where(User.id == victim.id).execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        assert fresh is not None
        assert fresh.is_superuser is False


class TestDeleteUser:
    @pytest.mark.asyncio
    async def test_regular_user_cannot_delete_others(self, client, db):
        actor = await _user(db)
        victim = await _user(db)

        response = client.delete(f"/api/v1/users/{victim.id}", headers=_headers(actor))
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_can_delete_user(self, client, db):
        admin = await _user(db, superuser=True)
        victim = await _user(db)

        response = client.delete(f"/api/v1/users/{victim.id}", headers=_headers(admin))
        assert response.status_code == 204

        user = (
            await db.execute(
                select(User).where(User.id == victim.id).execution_options(populate_existing=True)
            )
        ).scalar_one_or_none()
        assert user is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])