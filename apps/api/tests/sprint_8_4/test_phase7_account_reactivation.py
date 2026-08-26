"""Sprint 8.4 Phase 7: Account Reactivation Tests

Acceptance criteria:
- /auth/account/restore re-activates the account (is_active=True) so the user
  can log in again after cancelling deletion.
- /users/me/restore works for inactive / deletion-pending users (not blocked by
  account-status enforcement).
- Deactivated accounts can be reactivated and log back in.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.security import create_access_token, get_password_hash
from api.models.iam import UserSession
from api.models.user import User


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """An active user with a known password."""
    user = User(
        email=f"phase7_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("mysecret123"),
        full_name="Phase 7 User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _request_deletion(db: AsyncSession, user: User, *, deactivate: bool = False):
    now = datetime.now(timezone.utc)
    user.deletion_requested_at = now
    user.scheduled_deletion_at = now + timedelta(days=7)
    user.deletion_reason = "user_request"
    if deactivate:
        user.is_active = False
    await db.commit()


async def _activate_session(db: AsyncSession, user: User) -> uuid.UUID:
    sid = uuid.uuid4()
    session = UserSession(
        id=sid,
        user_id=user.id,
        ip_address="127.0.0.1",
        user_agent="Test Agent",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(session)
    await db.commit()
    return sid


def _headers(user: User, session_id: uuid.UUID | None) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, token_id=session_id)}"}


class TestAuthAccountRestore:
    @pytest.mark.asyncio
    async def test_restore_reactivates_inactive_account(self, client, test_user, db):
        await _request_deletion(db, test_user, deactivate=True)

        response = client.post(
            "/api/v1/auth/account/restore",
            json={"email": test_user.email, "password": "mysecret123"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        await db.refresh(test_user)
        assert test_user.is_active is True
        assert test_user.deletion_requested_at is None
        assert test_user.scheduled_deletion_at is None
        assert test_user.deletion_reason is None

    @pytest.mark.asyncio
    async def test_restore_requires_correct_password(self, client, test_user, db):
        await _request_deletion(db, test_user)
        response = client.post(
            "/api/v1/auth/account/restore",
            json={"email": test_user.email, "password": "wrongpassword"},
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_restore_without_deletion_request_rejected(self, client, test_user, db):
        response = client.post(
            "/api/v1/auth/account/restore",
            json={"email": test_user.email, "password": "mysecret123"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_restore_expired_grace_period_rejected(self, client, test_user, db):
        now = datetime.now(timezone.utc)
        test_user.deletion_requested_at = now - timedelta(days=30)
        test_user.scheduled_deletion_at = now - timedelta(days=23)
        await db.commit()

        response = client.post(
            "/api/v1/auth/account/restore",
            json={"email": test_user.email, "password": "mysecret123"},
        )
        assert response.status_code == 400


class TestMeRestore:
    @pytest.mark.asyncio
    async def test_me_restore_allowed_for_inactive_user(self, client, test_user, db):
        await _request_deletion(db, test_user, deactivate=True)
        sid = await _activate_session(db, test_user)

        response = client.post(
            "/api/v1/users/me/restore",
            headers=_headers(test_user, sid),
        )
        assert response.status_code == 200

        await db.refresh(test_user)
        assert test_user.is_active is True
        assert test_user.deletion_requested_at is None

    @pytest.mark.asyncio
    async def test_me_restore_without_deletion_request_rejected(self, client, test_user, db):
        sid = await _activate_session(db, test_user)
        response = client.post(
            "/api/v1/users/me/restore",
            headers=_headers(test_user, sid),
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_me_restore_requires_authentication(self, client):
        response = client.post("/api/v1/users/me/restore")
        assert response.status_code == 401


class TestDeactivationReactivate:
    @pytest.mark.asyncio
    async def test_reactivate_deactivated_account(self, client, test_user, db):
        test_user.is_active = False
        test_user.deactivated_at = datetime.now(timezone.utc)
        await db.commit()

        response = client.post(
            "/api/v1/account/lifecycle/reactivate",
            json={"email": test_user.email},
        )
        assert response.status_code == 200

        await db.refresh(test_user)
        assert test_user.is_active is True
        assert test_user.deactivated_at is None

    @pytest.mark.asyncio
    async def test_reactivated_user_can_login(self, client, test_user, db, monkeypatch):
        monkeypatch.setattr(
            "api.routes.auth.resolve_location",
            lambda ip: {"city": "Localhost", "country": "Localhost", "country_code": "LH"},
        )
        test_user.is_active = False
        test_user.deactivated_at = datetime.now(timezone.utc)
        await db.commit()

        client.post(
            "/api/v1/account/lifecycle/reactivate",
            json={"email": test_user.email},
        )

        login = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "mysecret123"},
        )
        assert login.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])