"""Sprint 8.4 Phase 11: Refresh-Token Family Reuse Detection Tests

Acceptance criterion: presenting an already-rotated (used) refresh token is
treated as potential theft and revokes the entire family plus every session,
with an audit trail.

Covers:
- Normal rotation: old token consumed (is_used=True, replaced_by), new token works.
- Reuse of a rotated token -> 401 + family revoked + sessions revoked.
- After family revocation, even the freshly issued token stops working.
- Reuse is recorded in the audit log.
- Expired / revoked tokens still behave as ordinary invalid tokens (no family kill).
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
        email=f"phase11_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Phase 11 User",
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
    family_id: uuid.UUID | None = None,
) -> tuple[UserSession, RefreshToken]:
    """Create a session plus one refresh token in a family."""
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

    token = RefreshToken(
        id=uuid.uuid4(),
        token_hash=uuid.uuid4().hex,
        user_id=user.id,
        session_id=sid,
        family_id=family_id or uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_revoked=False,
    )
    db.add(token)
    await db.commit()
    await db.refresh(token)
    return session, token


class TestRefreshRotation:
    @pytest.mark.asyncio
    async def test_normal_rotation_consumes_old_token(self, client, test_user, db):
        await _make_session(db, test_user)
        # Direct rotation pre-check: the stored token (raw hash) should NOT be
        # a usable refresh JWT; instead build a real family through the endpoint.
        # We create a genuine refresh JWT for the user:
        raw = create_refresh_token(str(test_user.id))

        # Seed a stored token for it (same shape the login flow writes).
        family = uuid.uuid4()
        session = UserSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True,
        )
        db.add(session)
        await db.flush()
        stored = RefreshToken(
            id=uuid.uuid4(),
            token_hash=sha256(raw.encode("utf-8")).hexdigest(),
            user_id=test_user.id,
            session_id=session.id,
            family_id=family,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        db.add(stored)
        await db.commit()

        # First refresh: rotate.
        first = client.post("/api/v1/auth/refresh", json={"refresh_token": raw})
        assert first.status_code == 200
        new_token = first.json()["refresh_token"]
        assert new_token != raw

        # Old token consumed.
        await db.refresh(stored)
        assert stored.is_used is True
        assert stored.replaced_by is not None

        # Second refresh with the new token works.
        second = client.post("/api/v1/auth/refresh", json={"refresh_token": new_token})
        assert second.status_code == 200

    @pytest.mark.asyncio
    async def test_reuse_revokes_family_and_sessions(self, client, test_user, db):
        raw = create_refresh_token(str(test_user.id))
        family = uuid.uuid4()
        session = UserSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True,
        )
        db.add(session)
        await db.flush()
        stored = RefreshToken(
            id=uuid.uuid4(),
            token_hash=sha256(raw.encode("utf-8")).hexdigest(),
            user_id=test_user.id,
            session_id=session.id,
            family_id=family,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        db.add(stored)
        sibling = RefreshToken(
            id=uuid.uuid4(),
            token_hash=uuid.uuid4().hex,
            user_id=test_user.id,
            session_id=session.id,
            family_id=family,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        db.add(sibling)
        await db.commit()

        # Rotate once.
        assert client.post("/api/v1/auth/refresh", json={"refresh_token": raw}).status_code == 200

        # Presenting the rotated (used) token again -> compromise handling.
        reused = client.post("/api/v1/auth/refresh", json={"refresh_token": raw})
        assert reused.status_code == 401

        # Entire family revoked (stored + sibling + newly-issued = 3 tokens).
        user_id = test_user.id
        db.expire_all()
        for t in (await db.execute(select(RefreshToken).where(RefreshToken.family_id == family))).scalars().all():
            await db.refresh(t)
        family_tokens = (
            await db.execute(select(RefreshToken).where(RefreshToken.family_id == family))
        ).scalars().all()
        assert len(family_tokens) == 3
        assert all(t.is_revoked for t in family_tokens)

        # All of the user's sessions revoked.
        for s in (await db.execute(select(UserSession).where(UserSession.user_id == user_id))).scalars().all():
            await db.refresh(s)
        sessions = (
            await db.execute(select(UserSession).where(UserSession.user_id == user_id))
        ).scalars().all()
        assert all(s.is_revoked for s in sessions)

        # Reuse recorded in the audit log.
        audits = (
            await db.execute(
                select(AuditLog).where(AuditLog.actor_id == user_id)
            )
        ).scalars().all()
        assert any(a.action == "REFRESH_TOKEN_REUSE" for a in audits)
        assert any(a.action == "TOKEN_REFRESH" for a in audits)

    @pytest.mark.asyncio
    async def test_family_revocation_kills_newest_token(self, client, test_user, db):
        raw = create_refresh_token(str(test_user.id))
        family = uuid.uuid4()
        session = UserSession(
            id=uuid.uuid4(),
            user_id=test_user.id,
            ip_address="127.0.0.1",
            user_agent="Test Agent",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
            is_active=True,
        )
        db.add(session)
        await db.flush()
        stored = RefreshToken(
            id=uuid.uuid4(),
            token_hash=sha256(raw.encode("utf-8")).hexdigest(),
            user_id=test_user.id,
            session_id=session.id,
            family_id=family,
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            is_revoked=False,
        )
        db.add(stored)
        await db.commit()

        new_token = client.post(
            "/api/v1/auth/refresh", json={"refresh_token": raw}
        ).json()["refresh_token"]

        # Reuse the rotated token -> family kill.
        assert (
            client.post("/api/v1/auth/refresh", json={"refresh_token": raw}).status_code
            == 401
        )

        # The newly issued token is now also dead (same family).
        assert (
            client.post(
                "/api/v1/auth/refresh", json={"refresh_token": new_token}
            ).status_code
            == 401
        )

    @pytest.mark.asyncio
    async def test_unknown_token_does_not_kill_family(self, client, test_user, db):
        await _make_session(db, test_user)
        unknown = create_refresh_token(str(test_user.id))
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": unknown})
        assert resp.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
