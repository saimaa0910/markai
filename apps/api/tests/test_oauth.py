"""
Tests: Google OAuth Integration
=================================
Tests Google OAuth token exchange, account linking, user creation, and failure cases.
"""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database.session import get_db
from api.database.base import Base
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


class TestGoogleOAuth:
    def test_google_oauth_creates_new_user_and_org(self, client, db):
        """Mock token creates new user record and default org."""
        res = client.post("/api/v1/auth/oauth/google", json={
            "access_token": "mock_new_oauth_user"
        })

        assert res.status_code == 200
        data = res.json()
        assert "access_token" in data
        assert "refresh_token" in data

        user = db.query(User).filter(User.email == "new_oauth_user@example.com").first()
        assert user is not None
        assert user.is_verified is True

        membership = db.query(UserOrganization).filter(UserOrganization.user_id == user.id).first()
        assert membership is not None
        assert membership.role == UserRole.OWNER

    def test_google_oauth_links_existing_user(self, client, db):
        """Existing user with matching email logs in via Google."""
        existing_user = User(
            email="existing_user@example.com",
            full_name="Existing User",
            is_active=True,
            is_verified=True,
        )
        db.add(existing_user)
        db.commit()

        res = client.post("/api/v1/auth/oauth/google", json={
            "access_token": "mock_existing_user"
        })

        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_google_oauth_invalid_provider_returns_400(self, client):
        """Unsupported provider returns HTTP 400."""
        res = client.post("/api/v1/auth/oauth/unsupported_provider", json={
            "access_token": "mock_token"
        })
        assert res.status_code == 400

    def test_google_oauth_missing_token_returns_422(self, client):
        """Empty payload returns HTTP 422 validation error."""
        res = client.post("/api/v1/auth/oauth/google", json={})
        assert res.status_code == 422
