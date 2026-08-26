"""Sprint 8.4 Phase 2: Logout Session Revocation Tests

Acceptance criterion: "Logout actually revokes the active session."

Covers:
- Revoking the active UserSession (is_revoked / revoked_at / revocation_reason).
- Revoking every refresh token bound to the session.
- Isolation from other sessions (only the current session is revoked).
- Post-logout rejection: access token and refresh token both stop working.
- Fallback path: a token without a resolvable session revokes all user tokens.
- Audit trail, logout-all, auth requirement, and full login -> logout E2E.
"""
import uuid
from datetime import datetime, timedelta, timezone
from hashlib import sha256

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.security import create_access_token, create_refresh_token, get_password_hash
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
        email=f"phase2_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Phase 2 User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _make_session(
    db: AsyncSession,
    user: User,
    *,
    session_id: uuid.UUID | None = None,
    token_count: int = 1,
) -> tuple[UserSession, list[RefreshToken]]:
    """Create a UserSession plus `token_count` un-revoked refresh tokens."""
    sid = session_id or uuid.uuid4()
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

    tokens = []
    for _ in range(token_count):
        token = RefreshToken(
            token_hash=uuid.uuid4().hex,
            user_id=user.id,
            session_id=sid,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        db.add(token)
        tokens.append(token)
    await db.commit()
    for t in tokens:
        await db.refresh(t)
    return session, tokens


def _auth_headers(user: User, session_id: uuid.UUID | None) -> dict:
    token = create_access_token(user.id, token_id=session_id)
    return {"Authorization": f"Bearer {token}"}


async def _stored_refresh_token(db: AsyncSession, raw_token: str) -> RefreshToken:
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == sha256(raw_token.encode()).hexdigest())
    )
    return result.scalar_one()


# ─── Core acceptance criterion ────────────────────────────────────────────────

class TestLogoutRevokesActiveSession:
    @pytest.mark.asyncio
    async def test_logout_revokes_session_and_tokens(self, client, test_user, db):
        session, (token,) = await _make_session(db, test_user)

        response = client.post(
            "/api/v1/auth/logout",
            headers=_auth_headers(test_user, session.id),
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

        await db.refresh(session)
        await db.refresh(token)
        assert session.is_revoked is True
        assert session.revoked_at is not None
        assert session.revocation_reason == "logout"
        assert token.is_revoked is True

    @pytest.mark.asyncio
    async def test_logout_revokes_every_token_in_the_session(self, client, test_user, db):
        session, tokens = await _make_session(db, test_user, token_count=4)

        response = client.post(
            "/api/v1/auth/logout",
            headers=_auth_headers(test_user, session.id),
        )

        assert response.status_code == 200
        for token in tokens:
            await db.refresh(token)
            assert token.is_revoked is True

    @pytest.mark.asyncio
    async def test_logout_only_revokes_the_current_session(self, client, test_user, db):
        session_a, _ = await _make_session(db, test_user)
        session_b, tokens_b = await _make_session(db, test_user)

        response = client.post(
            "/api/v1/auth/logout",
            headers=_auth_headers(test_user, session_a.id),
        )

        assert response.status_code == 200

        await db.refresh(session_a)
        await db.refresh(session_b)
        assert session_a.is_revoked is True
        assert session_b.is_revoked is False

        # Session B's refresh tokens must remain untouched...
        for token in tokens_b:
            await db.refresh(token)
            assert token.is_revoked is False

        # ...and session B's access token still works on a protected endpoint.
        me = client.get("/api/v1/auth/me", headers=_auth_headers(test_user, session_b.id))
        assert me.status_code == 200


# ─── Post-logout rejection ────────────────────────────────────────────────────

class TestPostLogoutRejection:
    @pytest.mark.asyncio
    async def test_access_token_rejected_after_logout(self, client, test_user, db):
        session, _ = await _make_session(db, test_user)

        client.post(
            "/api/v1/auth/logout",
            headers=_auth_headers(test_user, session.id),
        )

        # The same access token must now be rejected on a protected endpoint.
        response = client.get("/api/v1/auth/me", headers=_auth_headers(test_user, session.id))
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token_rejected_after_logout(self, client, test_user, db):
        session, _ = await _make_session(db, test_user)
        # A real (signed) refresh token for this user, stored for the session.
        raw_refresh = create_refresh_token(test_user.id)
        db.add(RefreshToken(
            token_hash=sha256(raw_refresh.encode()).hexdigest(),
            user_id=test_user.id,
            session_id=session.id,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        ))
        await db.commit()

        client.post(
            "/api/v1/auth/logout",
            headers=_auth_headers(test_user, session.id),
        )

        stored = await _stored_refresh_token(db, raw_refresh)
        assert stored.is_revoked is True

        # Rotation with the revoked token must fail.
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_refresh},
        )
        assert response.status_code in (401, 422)

    @pytest.mark.asyncio
    async def test_second_logout_attempt_is_rejected(self, client, test_user, db):
        session, _ = await _make_session(db, test_user)
        headers = _auth_headers(test_user, session.id)

        first = client.post("/api/v1/auth/logout", headers=headers)
        assert first.status_code == 200

        second = client.post("/api/v1/auth/logout", headers=headers)
        assert second.status_code == 401


# ─── Fallback / auth requirements ─────────────────────────────────────────────

class TestLogoutFallbackAndAuth:
    @pytest.mark.asyncio
    async def test_logout_without_resolvable_session_revokes_all_tokens(self, client, test_user, db):
        _, tokens_a = await _make_session(db, test_user)
        _, tokens_b = await _make_session(db, test_user)

        # Access token with a jti that matches no session (token_id omitted).
        headers = _auth_headers(test_user, None)
        response = client.post("/api/v1/auth/logout", headers=headers)

        assert response.status_code == 200
        for token in tokens_a + tokens_b:
            await db.refresh(token)
            assert token.is_revoked is True

    @pytest.mark.asyncio
    async def test_logout_requires_authentication(self, client):
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_records_audit_event(self, client, test_user, db):
        session, _ = await _make_session(db, test_user)

        response = client.post(
            "/api/v1/auth/logout",
            headers=_auth_headers(test_user, session.id),
        )
        assert response.status_code == 200

        result = await db.execute(
            select(AuditLog).where(
                AuditLog.action == "USER_LOGOUT",
                AuditLog.actor_id == test_user.id,
            )
        )
        audit = result.scalars().first()
        assert audit is not None
        assert audit.entity_type == "users"


# ─── Logout-all ───────────────────────────────────────────────────────────────

class TestLogoutAll:
    @pytest.mark.asyncio
    async def test_logout_all_revokes_all_sessions_and_tokens(self, client, test_user, db):
        session_a, tokens_a = await _make_session(db, test_user)
        session_b, tokens_b = await _make_session(db, test_user)

        response = client.post(
            "/api/v1/auth/logout-all",
            headers=_auth_headers(test_user, session_a.id),
        )

        assert response.status_code == 200

        for session in (session_a, session_b):
            await db.refresh(session)
            assert session.is_revoked is True
            assert session.revocation_reason == "logout_all"

        for token in tokens_a + tokens_b:
            await db.refresh(token)
            assert token.is_revoked is True


# ─── End-to-end: login -> logout ──────────────────────────────────────────────

class TestLogoutEndToEnd:
    @pytest.mark.asyncio
    async def test_login_then_logout_revokes_the_created_session(
        self, client, test_user, db, monkeypatch
    ):
        # Avoid any network IP-geolocation during the login alert flow.
        monkeypatch.setattr(
            "api.routes.auth.resolve_location",
            lambda ip: {
                "city": "Localhost",
                "country": "Localhost",
                "country_code": "LH",
            },
        )

        password = "Sup3rSecret!"
        test_user.hashed_password = get_password_hash(password)
        await db.commit()

        login = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": password},
        )
        assert login.status_code == 200
        tokens = login.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # The session created by login is active and the refresh token is stored.
        stored = await _stored_refresh_token(db, refresh_token)
        assert stored.is_revoked is False
        session = await db.get(UserSession, stored.session_id)
        assert session is not None
        assert session.is_revoked is False

        # Logout using the access token from login.
        response = client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200

        await db.refresh(session)
        await db.refresh(stored)
        assert session.is_revoked is True
        assert session.revocation_reason == "logout"
        assert stored.is_revoked is True

        # Both tokens are now dead.
        me = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me.status_code == 401

        refresh_call = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_call.status_code in (401, 422)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
