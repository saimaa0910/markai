"""Phase 2 regression: logout revokes the current session and its refresh tokens."""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.security import create_access_token, get_password_hash
from api.models.iam import RefreshToken, UserSession
from api.models.user import User


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    user = User(
        email=f"p2_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Phase2 User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_logout_revokes_current_session_and_refresh_token(client, test_user, db):
    session_id = uuid.uuid4()
    session = UserSession(
        id=session_id,
        user_id=test_user.id,
        ip_address="127.0.0.1",
        user_agent="Test Agent",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(session)
    await db.flush()
    refresh = RefreshToken(
        token_hash=uuid.uuid4().hex,
        user_id=test_user.id,
        session_id=session_id,
        family_id=uuid.uuid4(),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        is_revoked=False,
    )
    db.add(refresh)
    await db.commit()

    token = create_access_token(test_user.id, token_id=session_id)
    response = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200

    await db.refresh(session)
    await db.refresh(refresh)
    assert session.is_revoked is True
    assert session.revoked_at is not None
    assert session.revocation_reason == "logout"
    assert refresh.is_revoked is True
