"""Sprint 8.4 Phase 5 & 6: Temporary Password System + Force Password Change Tests

Phase 5 acceptance criteria:
- Invite flow stores temp-password state in the EXPLICIT User columns that the
  enforcement middleware reads (not only metadata_json).
- Invited users can sign in with the temporary password.

Phase 6 acceptance criteria:
- Users flagged with change_password_required are blocked from protected routes.
- The change-password endpoint itself is exempt from the block.
- Completing a password change clears the flag and unblocks the account.
- An expired temporary password blocks the account until a new invitation.
"""
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.core.security import create_access_token, get_password_hash
from api.models.membership import OrganizationInvitation, UserOrganization, UserRole
from api.models.organization import Organization
from api.models.iam import UserSession
from api.models.user import User


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def test_owner(db: AsyncSession):
    """An active user who will OWN the organization."""
    user = User(
        email=f"owner_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("ownerpass123"),
        full_name="Org Owner",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    org = Organization(name="Test Org", slug=f"test-org-{uuid.uuid4().hex[:8]}")
    db.add(org)
    await db.commit()
    await db.refresh(org)

    membership = UserOrganization(
        user_id=user.id,
        organization_id=org.id,
        role=UserRole.OWNER,
    )
    db.add(membership)
    await db.commit()
    return user, org


def _headers(user: User, session_id: uuid.UUID | None = None) -> dict:
    return {"Authorization": f"Bearer {create_access_token(user.id, token_id=session_id)}"}


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


async def _make_temp_user(
    db: AsyncSession,
    *,
    temp_expires: datetime | None = None,
    change_required: bool = True,
) -> tuple[User, str]:
    """Create a user in the same state the invite flow produces."""
    temp_password = "TempInvite123!"
    user = User(
        email=f"temp_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash(temp_password),
        full_name="Invited User",
        is_active=True,
        is_verified=False,
        change_password_required=change_required,
        temporary_password=get_password_hash(temp_password),
        temporary_password_expires_at=temp_expires
        or (datetime.now(timezone.utc) + timedelta(hours=72)),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user, temp_password


class TestPhase5TempPasswordColumns:
    @pytest.mark.asyncio
    async def test_invite_stores_explicit_temp_password_columns(
        self, client, test_owner, db
    ):
        owner, org = test_owner
        email = f"invited_{uuid.uuid4()}@example.com"

        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations/",
            json={"email": email, "role": "MEMBER"},
            headers=_headers(owner),
        )
        assert response.status_code == 200

        invited = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        assert invited is not None
        # Phase 5: explicit columns are populated (enforcement reads these).
        assert invited.change_password_required is True
        assert invited.temporary_password is not None
        assert invited.temporary_password_expires_at is not None
        assert invited.temporary_password_expires_at > datetime.now(timezone.utc)
        assert invited.is_verified is False
        # Frontend compatibility metadata kept.
        meta = invited.metadata_json or {}
        assert meta.get("change_password_required") is True

        # An invitation row was created.
        invite = (
            await db.execute(
                select(OrganizationInvitation).where(
                    OrganizationInvitation.email == email,
                    OrganizationInvitation.organization_id == org.id,
                )
            )
        ).scalar_one_or_none()
        assert invite is not None

    @pytest.mark.asyncio
    async def test_invited_user_can_login_with_temporary_password(
        self, client, test_owner, db, monkeypatch
    ):
        monkeypatch.setattr(
            "api.routes.auth.resolve_location",
            lambda ip: {"city": "Localhost", "country": "Localhost", "country_code": "LH"},
        )
        owner, org = test_owner
        email = f"invited_{uuid.uuid4()}@example.com"
        temp_password = "AdminSetTemp123!"

        response = client.post(
            f"/api/v1/organizations/{org.id}/invitations/",
            json={"email": email, "role": "MEMBER", "temporary_password": temp_password},
            headers=_headers(owner),
        )
        assert response.status_code == 200

        invited = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
        assert invited is not None

        # The admin-set temporary password signs the invited user in.
        login = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": temp_password},
        )
        assert login.status_code == 200
        tokens = login.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # A wrong password is still rejected.
        login_bad = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "definitely-wrong"},
        )
        assert login_bad.status_code == 401


class TestPhase6ForcePasswordChange:
    @pytest.mark.asyncio
    async def test_change_password_required_blocks_protected_routes(
        self, client, db
    ):
        user, temp_password = await _make_temp_user(db)
        sid = await _activate_session(db, user)

        response = client.get(
            "/api/v1/sessions",
            headers=_headers(user, sid),
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "password_change_required"

    @pytest.mark.asyncio
    async def test_change_password_endpoint_is_exempt(self, client, db):
        user, temp_password = await _make_temp_user(db)
        sid = await _activate_session(db, user)

        response = client.post(
            "/api/v1/auth/change-password",
            json={"temporary_password": temp_password, "new_password": "RealPass123!"},
            headers=_headers(user, sid),
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_change_password_clears_flag_and_unblocks(self, client, db):
        user, temp_password = await _make_temp_user(db)
        sid = await _activate_session(db, user)

        change = client.post(
            "/api/v1/auth/change-password",
            json={"temporary_password": temp_password, "new_password": "RealPass123!"},
            headers=_headers(user, sid),
        )
        assert change.status_code == 200

        await db.refresh(user)
        assert user.change_password_required is False
        assert user.temporary_password is None

        # The account is unblocked on protected routes.
        response = client.get("/api/v1/sessions", headers=_headers(user, sid))
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_expired_temporary_password_blocks_protected_routes(self, client, db):
        user, _ = await _make_temp_user(
            db,
            temp_expires=datetime.now(timezone.utc) - timedelta(hours=1),
            change_required=False,
        )
        sid = await _activate_session(db, user)

        response = client.get(
            "/api/v1/sessions",
            headers=_headers(user, sid),
        )
        assert response.status_code == 403
        assert response.json()["detail"]["error"] == "temporary_password_expired"

    @pytest.mark.asyncio
    async def test_expired_temporary_password_cannot_change_password(self, client, db):
        user, temp_password = await _make_temp_user(
            db, temp_expires=datetime.now(timezone.utc) - timedelta(hours=1)
        )
        sid = await _activate_session(db, user)

        response = client.post(
            "/api/v1/auth/change-password",
            json={"temporary_password": temp_password, "new_password": "RealPass123!"},
            headers=_headers(user, sid),
        )
        assert response.status_code == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])