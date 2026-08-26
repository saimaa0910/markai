"""Sprint 8.3.1 Phase 1: Session Management Tests

Comprehensive test suite for session management features.
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from api.main import app
from api.models.user import User
from api.models.iam import UserSession as Session
from api.services.iam.session_service import SessionService
from api.core.security import create_access_token, get_password_hash


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
async def test_user(db: AsyncSession):
    """Create a test user."""
    user = User(
        email=f"test_{uuid.uuid4()}@example.com",
        hashed_password=get_password_hash("testpassword"),
        full_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def sample_session(db: AsyncSession, test_user: User):
    """Create a test session."""
    session = Session(
        user_id=test_user.id,
        session_token=str(uuid.uuid4()),
        ip_address="127.0.0.1",
        user_agent="Test Agent",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        is_active=True,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


class TestSessionListing:
    """Test GET /api/v1/auth/sessions endpoint."""
    
    @pytest.mark.asyncio
    async def test_list_sessions_success(self, client, test_user, sample_session, db):
        """Test listing user sessions successfully."""
        # Create access token
        token = create_access_token(data={"sub": str(test_user.id)})
        
        # Request sessions
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data
        assert len(data["sessions"]) >= 1
        assert data["sessions"][0]["id"] == str(sample_session.id)
    
    @pytest.mark.asyncio
    async def test_list_sessions_unauthorized(self, client):
        """Test listing sessions without authentication."""
        response = client.get("/api/v1/auth/sessions")
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_list_sessions_includes_current(self, client, test_user, db):
        """Test that current session is included in list."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert any(s.get("is_current") for s in data["sessions"])


class TestSessionRevocation:
    """Test DELETE /api/v1/auth/sessions/{id} endpoint."""
    
    @pytest.mark.asyncio
    async def test_revoke_session_success(self, client, test_user, sample_session, db):
        """Test revoking a specific session."""
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.delete(
            f"/api/v1/auth/sessions/{sample_session.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 204
        
        # Verify session is revoked
        await db.refresh(sample_session)
        assert not sample_session.is_active
        assert sample_session.revoked_at is not None
    
    @pytest.mark.asyncio
    async def test_revoke_session_not_found(self, client, test_user):
        """Test revoking non-existent session."""
        token = create_access_token(data={"sub": str(test_user.id)})
        fake_id = uuid.uuid4()
        
        response = client.delete(
            f"/api/v1/auth/sessions/{fake_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 404
    
    @pytest.mark.asyncio
    async def test_revoke_other_user_session(self, client, test_user, sample_session, db):
        """Test that users cannot revoke other users' sessions."""
        # Create another user
        other_user = User(
            email=f"other_{uuid.uuid4()}@example.com",
            hashed_password=get_password_hash("password"),
            full_name="Other User",
            is_active=True,
        )
        db.add(other_user)
        await db.commit()
        
        # Try to revoke test_user's session as other_user
        token = create_access_token(data={"sub": str(other_user.id)})
        response = client.delete(
            f"/api/v1/auth/sessions/{sample_session.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 403


class TestRevokeAllSessions:
    """Test DELETE /api/v1/auth/sessions/all endpoint."""
    
    @pytest.mark.asyncio
    async def test_revoke_all_sessions_success(self, client, test_user, db):
        """Test revoking all user sessions."""
        # Create multiple sessions
        sessions = []
        for _ in range(3):
            session = Session(
                user_id=test_user.id,
                session_token=str(uuid.uuid4()),
                ip_address="127.0.0.1",
                user_agent="Test Agent",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                is_active=True,
            )
            db.add(session)
            sessions.append(session)
        await db.commit()
        
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.delete(
            "/api/v1/auth/sessions/all",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["revoked_count"] >= 3
        
        # Verify all sessions are revoked
        for session in sessions:
            await db.refresh(session)
            assert not session.is_active
    
    @pytest.mark.asyncio
    async def test_revoke_all_excludes_current(self, client, test_user, sample_session, db):
        """Test that revoking all sessions excludes current session."""
        # This depends on implementation - some systems keep current session active
        token = create_access_token(data={"sub": str(test_user.id)})
        
        response = client.delete(
            "/api/v1/auth/sessions/all",
            headers={"Authorization": f"Bearer {token}"},
            params={"except_current": True},
        )
        
        assert response.status_code == 200
        
        # Current session should still be active
        await db.refresh(sample_session)
        assert sample_session.is_active


class TestSessionService:
    """Test SessionService methods."""
    
    @pytest.mark.asyncio
    async def test_create_session(self, db, test_user):
        """Test creating a new session."""
        session_data = await SessionService.create_session_row(
            db=db,
            user_id=test_user.id,
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            device_info={"type": "desktop", "os": "Windows"},
        )
        
        assert session_data["user_id"] == str(test_user.id)
        assert session_data["ip_address"] == "192.168.1.1"
        assert "session_token" in session_data
    
    @pytest.mark.asyncio
    async def test_get_user_sessions(self, db, test_user, sample_session):
        """Test retrieving user sessions."""
        sessions = await SessionService.get_user_sessions(
            db=db,
            user_id=test_user.id,
            include_revoked=False,
        )
        
        assert len(sessions) >= 1
        assert any(s["id"] == str(sample_session.id) for s in sessions)
    
    @pytest.mark.asyncio
    async def test_revoke_session(self, db, test_user, sample_session):
        """Test revoking a session."""
        await SessionService.revoke_session_row(
            db=db,
            session_id=sample_session.id,
            user_id=test_user.id,
        )
        
        await db.refresh(sample_session)
        assert not sample_session.is_active
        assert sample_session.revoked_at is not None
    
    @pytest.mark.asyncio
    async def test_revoke_all_sessions(self, db, test_user):
        """Test revoking all user sessions."""
        # Create multiple sessions
        for _ in range(3):
            session = Session(
                user_id=test_user.id,
                session_token=str(uuid.uuid4()),
                ip_address="127.0.0.1",
                user_agent="Test",
                expires_at=datetime.now(timezone.utc) + timedelta(days=7),
                is_active=True,
            )
            db.add(session)
        await db.commit()
        
        count = await SessionService.revoke_all_sessions(
            db=db,
            user_id=test_user.id,
        )
        
        assert count >= 3
    
    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, db, test_user):
        """Test cleaning up expired sessions."""
        # Create expired session
        expired_session = Session(
            user_id=test_user.id,
            session_token=str(uuid.uuid4()),
            ip_address="127.0.0.1",
            user_agent="Test",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
            is_active=True,
        )
        db.add(expired_session)
        await db.commit()
        
        deleted_count = await SessionService.cleanup_expired_sessions(db)
        
        assert deleted_count >= 1


class TestSessionSecurity:
    """Test session security features."""
    
    @pytest.mark.asyncio
    async def test_session_expiration_enforced(self, client, test_user, db):
        """Test that expired sessions are rejected."""
        # Create expired session
        expired_session = Session(
            user_id=test_user.id,
            session_token=str(uuid.uuid4()),
            ip_address="127.0.0.1",
            user_agent="Test",
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
            is_active=True,
        )
        db.add(expired_session)
        await db.commit()
        
        # Try to use expired session
        token = create_access_token(data={
            "sub": str(test_user.id),
            "session_id": str(expired_session.id),
        })
        
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        # Should be rejected
        assert response.status_code == 401
    
    @pytest.mark.asyncio
    async def test_revoked_session_rejected(self, client, test_user, sample_session, db):
        """Test that revoked sessions are rejected."""
        # Revoke session
        sample_session.is_active = False
        sample_session.revoked_at = datetime.now(timezone.utc)
        await db.commit()
        
        # Try to use revoked session
        token = create_access_token(data={
            "sub": str(test_user.id),
            "session_id": str(sample_session.id),
        })
        
        response = client.get(
            "/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
