"""Sprint 8.4 Phase 4: Change-Password Consolidation Tests

Acceptance criteria:
- Exactly ONE canonical change-password implementation is reachable.
- Regular change requires the current password.
- Temporary-password (first login) flow works and clears enforcement flags.
- Changing the password revokes all OTHER sessions but keeps the current one.
- The legacy /auth/password-change alias is gone.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.security import create_access_token, get_password_hash, verify_password
from api.models.iam import RefreshToken, UserSession
from api.models.platform_events import AuditLog
from api.models.user import User


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create an active, verified test user."""
    user = User(
        email=f"phase4_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("current-pass"),
        full_name="Phase 4 User",
        is_active=True,
        is_verified=True,
        change_password_required=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _make_session(db: AsyncSession, user: User) -> UserSession:
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
    await db.flush()
    db.add(RefreshToken(
        token_hash=uuid.uuid4().hex,
        user_id=user.id,
        session_id=sid,
        family_id=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_revoked=False,
    ))
    await db.commit()
    await db.refresh(session)
    return session


def _headers(user: User, session_id: uuid.UUID | None) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, token_id=session_id)}"}


class TestCanonicalRoute:
    def test_only_one_change_password_route_registered(self):
        schema = app.openapi()
        paths = schema["paths"]
        # Exactly one POST operation is reachable under the canonical path.
        assert paths.get("/api/v1/auth/change-password", {}).get("post") is not None
        # The duplicated legacy alias must be gone.
        assert "/api/v1/auth/password-change" not in paths

    @pytest.mark.asyncio
    async def test_legacy_alias_removed(self, client, test_user, db):
        response = client.post(
            "/api/v1/auth/password-change",
            json={"old_password": "current-pass", "new_password": "NewPass123!"},
        )
        assert response.status_code == 404


class TestRegularChange:
    @pytest.mark.asyncio
    async def test_change_password_regular_flow(self, client, test_user, db):
        session = await _make_session(db, test_user)

        response = client.post(
            "/api/v1/auth/change-password",
            json={
                "current_password": "current-pass",
                "new_password": "brand-new-pass!",
            },
            headers=_headers(test_user, session.id),
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        await db.refresh(test_user)
        assert verify_password("brand-new-pass!", test_user.hashed_password) is True
        assert test_user.password_changed_at is not None

        # Change-password requirement flag stays cleared after a change.
        assert test_user.change_password_required is False

    @pytest.mark.asyncio
    async def test_change_password_wrong_current_password(self, client, test_user, db):
        session = await _make_session(db, test_user)
        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "wrong", "new_password": "NewPass123!"},
            headers=_headers(test_user, session.id),
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_requires_a_password_field(self, client, test_user, db):
        session = await _make_session(db, test_user)
        response = client.post(
            "/api/v1/auth/change-password",
            json={"new_password": "NewPass123!"},
            headers=_headers(test_user, session.id),
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_rejects_short_password(self, client, test_user, db):
        session = await _make_session(db, test_user)
        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "current-pass", "new_password": "short"},
            headers=_headers(test_user, session.id),
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_change_password_requires_authentication(self, client):
        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "x", "new_password": "NewPass123!"},
        )
        assert response.status_code == 401


class TestTemporaryPasswordFlow:
    @pytest.mark.asyncio
    async def test_temporary_password_first_login(self, client, test_user, db):
        test_user.change_password_required = True
        test_user.temporary_password = get_password_hash("TempPass123!")
        test_user.temporary_password_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        await db.commit()

        session = await _make_session(db, test_user)
        response = client.post(
            "/api/v1/auth/change-password",
            json={"temporary_password": "TempPass123!", "new_password": "MyNewPass456!"},
            headers=_headers(test_user, session.id),
        )
        assert response.status_code == 200

        await db.refresh(test_user)
        assert test_user.change_password_required is False
        assert test_user.temporary_password is None
        assert test_user.temporary_password_expires_at is None
        assert verify_password("MyNewPass456!", test_user.hashed_password) is True

    @pytest.mark.asyncio
    async def test_temporary_password_wrong_value(self, client, test_user, db):
        test_user.change_password_required = True
        test_user.temporary_password = get_password_hash("TempPass123!")
        test_user.temporary_password_expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
        await db.commit()

        session = await _make_session(db, test_user)
        response = client.post(
            "/api/v1/auth/change-password",
            json={"temporary_password": "Nope", "new_password": "MyNewPass456!"},
            headers=_headers(test_user, session.id),
        )
        assert response.status_code == 401


class TestSessionRevocation:
    @pytest.mark.asyncio
    async def test_change_password_revokes_other_sessions_only(self, client, test_user, db):
        session_a = await _make_session(db, test_user)
        session_b = await _make_session(db, test_user)

        result = await db.execute(
            select(RefreshToken).where(RefreshToken.session_id == session_b.id)
        )
        token_b = result.scalars().first()

        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "current-pass", "new_password": "NewPass123!"},
            headers=_headers(test_user, session_a.id),
        )
        assert response.status_code == 200

        # Session A (the one that changed the password) stays active.
        await db.refresh(session_a)
        assert session_a.is_revoked is False

        # Session B and its refresh token are revoked.
        await db.refresh(session_b)
        assert session_b.is_revoked is True
        assert session_b.revocation_reason == "password_change"
        await db.refresh(token_b)
        assert token_b.is_revoked is True

        # Session B's access token no longer works.
        me_b = client.get("/api/v1/auth/me", headers=_headers(test_user, session_b.id))
        assert me_b.status_code == 401

        # Session A's access token still works.
        me_a = client.get("/api/v1/auth/me", headers=_headers(test_user, session_a.id))
        assert me_a.status_code == 200


class TestAudit:
    @pytest.mark.asyncio
    async def test_change_password_records_audit_event(self, client, test_user, db):
        session = await _make_session(db, test_user)

        client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "current-pass", "new_password": "NewPass123!"},
            headers=_headers(test_user, session.id),
        )

        result = await db.execute(
            select(AuditLog).where(
                AuditLog.action == "PASSWORD_CHANGED",
                AuditLog.actor_id == test_user.id,
            )
        )
        audit = result.scalars().first()
        assert audit is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])