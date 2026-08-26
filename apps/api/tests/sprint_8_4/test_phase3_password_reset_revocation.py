"""Sprint 8.4 Phase 3: Password Reset Revocation Tests

Acceptance criterion: "Password reset revokes previous sessions."

Covers:
- Every UserSession is revoked on password reset (is_revoked / reason).
- Every refresh token is revoked.
- Old access tokens stop working immediately after the reset.
- Old refresh tokens cannot be rotated.
- The password hash actually changes (old password rejected).
- A fresh login with the new password works.
- Reset token is single-use; bad tokens are rejected.
- Audit trail entry is recorded.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from api.main import app
from api.core.security import create_access_token, create_refresh_token, get_password_hash, verify_password
from api.models.iam import RefreshToken, UserSession
from api.models.platform_events import AuditLog
from api.models.user import User
from api.routes.auth import _create_password_reset_token


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create an active, verified test user."""
    user = User(
        email=f"phase3_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("oldpassword"),
        full_name="Phase 3 User",
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
    token_count: int = 1,
) -> tuple[UserSession, list[RefreshToken]]:
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


def _reset_token(db_session: Session, user_id: uuid.UUID) -> str:
    """Create a raw password-reset token via the sync db session."""
    return _create_password_reset_token(db_session, user_id)


class TestPasswordResetRevokesSessions:
    @pytest.mark.asyncio
    async def test_reset_password_revokes_all_sessions_and_tokens(
        self, client, test_user, db, db_session
    ):
        session_a, tokens_a = await _make_session(db, test_user, token_count=2)
        session_b, tokens_b = await _make_session(db, test_user, token_count=1)
        raw = _reset_token(db_session, test_user.id)

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "NewPassword123!"},
        )
        assert response.status_code == 200

        for session in (session_a, session_b):
            await db.refresh(session)
            assert session.is_revoked is True
            assert session.revoked_at is not None
            assert session.revocation_reason == "password_reset"

        for token in tokens_a + tokens_b:
            await db.refresh(token)
            assert token.is_revoked is True

    @pytest.mark.asyncio
    async def test_access_tokens_invalid_after_password_reset(
        self, client, test_user, db, db_session
    ):
        session, _ = await _make_session(db, test_user)
        raw = _reset_token(db_session, test_user.id)

        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "NewPassword123!"},
        )
        assert response.status_code == 200

        me = client.get("/api/v1/auth/me", headers=_auth_headers(test_user, session.id))
        assert me.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_tokens_cannot_rotate_after_password_reset(
        self, client, test_user, db, db_session
    ):
        session, _ = await _make_session(db, test_user)
        raw_refresh = create_refresh_token(test_user.id)
        from hashlib import sha256

        db.add(RefreshToken(
            token_hash=sha256(raw_refresh.encode()).hexdigest(),
            user_id=test_user.id,
            session_id=session.id,
            family_id=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        ))
        await db.commit()

        raw = _reset_token(db_session, test_user.id)
        client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "NewPassword123!"},
        )

        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": raw_refresh},
        )
        assert response.status_code in (401, 422)


class TestPasswordResetPasswordChange:
    @pytest.mark.asyncio
    async def test_password_hash_changes_old_password_rejected(
        self, client, test_user, db, db_session
    ):
        raw = _reset_token(db_session, test_user.id)
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "CompletelyNew!1"},
        )
        assert response.status_code == 200

        await db.refresh(test_user)
        assert verify_password("oldpassword", test_user.hashed_password) is False
        assert verify_password("CompletelyNew!1", test_user.hashed_password) is True
        assert test_user.password_changed_at is not None

    @pytest.mark.asyncio
    async def test_new_login_works_after_password_reset(
        self, client, test_user, db, db_session, monkeypatch
    ):
        monkeypatch.setattr(
            "api.routes.auth.resolve_location",
            lambda ip: {"city": "Localhost", "country": "Localhost", "country_code": "LH"},
        )
        raw = _reset_token(db_session, test_user.id)
        client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "FreshPassword123"},
        )

        login = client.post(
            "/api/v1/auth/login",
            json={"email": test_user.email, "password": "FreshPassword123"},
        )
        assert login.status_code == 200
        tokens = login.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # New session created by the fresh login is active.
        from hashlib import sha256
        result = await db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == sha256(tokens["refresh_token"].encode()).hexdigest()
            )
        )
        stored = result.scalar_one()
        session = await db.get(UserSession, stored.session_id)
        assert session is not None
        assert session.is_revoked is False


class TestPasswordResetTokenSecurity:
    @pytest.mark.asyncio
    async def test_reset_token_is_single_use(self, client, test_user, db, db_session):
        raw = _reset_token(db_session, test_user.id)
        first = client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "FirstPass123!"},
        )
        assert first.status_code == 200

        second = client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "SecondPass123!"},
        )
        assert second.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_rejects_invalid_token(self, client, test_user):
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": "not-a-real-token", "new_password": "NewPassword123!"},
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_records_audit_event(
        self, client, test_user, db, db_session
    ):
        raw = _reset_token(db_session, test_user.id)
        response = client.post(
            "/api/v1/auth/reset-password",
            json={"token": raw, "new_password": "NewPassword123!"},
        )
        assert response.status_code == 200

        result = await db.execute(
            select(AuditLog).where(
                AuditLog.action == "PASSWORD_RESET_SUCCESS",
                AuditLog.actor_id == test_user.id,
            )
        )
        audit = result.scalars().first()
        assert audit is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
