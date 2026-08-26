"""
Tests: Email Verification Flow
=================================
Tests the DB-token-based email verification lifecycle.
"""
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.core.config import settings
from api.database.session import get_db
from api.database.base import Base
from api.models.user import User
from api.models.email_verification import EmailVerificationToken
from api.core.security import get_password_hash


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def unverified_user(db):
    user = User(
        email="unverified@example.com",
        hashed_password=get_password_hash("testpassword123"),
        full_name="Test User",
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestEmailVerificationTokenCreation:
    def test_token_created_on_register(self, client, db, monkeypatch):
        """Registration creates a DB verification token."""
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        with patch("api.routes.auth.send_verification_email", return_value=True):
            res = client.post("/api/v1/auth/register", json={
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "New User",
                "org_name": "Test Org",
            })
        assert res.status_code in (200, 201)
        user = db.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False,
        ).first()
        assert token is not None
        assert token.expires_at is not None

    def test_token_is_hashed_not_plaintext(self, client, db, monkeypatch):
        """Stored token_hash must be a SHA-256 hex (64 chars), not raw token."""
        monkeypatch.setattr(settings, "ENVIRONMENT", "development")
        with patch("api.routes.auth.send_verification_email", return_value=True):
            client.post("/api/v1/auth/register", json={
                "email": "hashed@example.com",
                "password": "password1234",
                "full_name": "Hash User",
                "org_name": "Hash Org",
            })
        user = db.query(User).filter(User.email == "hashed@example.com").first()
        token = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
        ).first()
        assert token is not None
        assert len(token.token_hash) == 64  # SHA-256 hex


class TestEmailVerification:
    def test_valid_token_verifies_email(self, client, db, unverified_user):
        """Valid token sets is_verified=True and marks token as used."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        db_token = EmailVerificationToken(
            user_id=unverified_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(db_token)
        db.commit()

        with patch("api.routes.auth.send_welcome_email", return_value=True):
            res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})

        assert res.status_code == 200
        db.refresh(unverified_user)
        db.refresh(db_token)
        assert unverified_user.is_verified is True
        assert db_token.is_used is True
        assert db_token.used_at is not None

    def test_expired_token_rejected(self, client, db, unverified_user):
        """Token past expiry returns 400."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        db_token = EmailVerificationToken(
            user_id=unverified_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
        )
        db.add(db_token)
        db.commit()

        res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        assert res.status_code == 400

    def test_used_token_rejected(self, client, db, unverified_user):
        """Already-used token returns 400."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        db_token = EmailVerificationToken(
            user_id=unverified_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            is_used=True,
        )
        db.add(db_token)
        db.commit()

        res = client.post("/api/v1/auth/verify-email", json={"token": raw_token})
        assert res.status_code == 400

    def test_invalid_token_rejected(self, client):
        """Random string token is rejected."""
        res = client.post("/api/v1/auth/verify-email", json={"token": "invalid_token_string"})
        assert res.status_code == 400

    def test_welcome_email_sent_on_verification(self, client, db, unverified_user):
        """Welcome email is sent after successful verification."""
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
        db.add(EmailVerificationToken(
            user_id=unverified_user.id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        ))
        db.commit()

        with patch("api.routes.auth.send_welcome_email", return_value=True) as mock_welcome:
            client.post("/api/v1/auth/verify-email", json={"token": raw_token})
            mock_welcome.assert_called_once()


class TestResendVerification:
    def test_resend_invalidates_old_token(self, client, db, unverified_user):
        """Resend creates new token and invalidates old ones."""
        old_raw = secrets.token_urlsafe(32)
        old_hash = hashlib.sha256(old_raw.encode()).hexdigest()
        old_token = EmailVerificationToken(
            user_id=unverified_user.id,
            token_hash=old_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
        )
        db.add(old_token)
        db.commit()

        with patch("api.routes.auth.send_verification_email", return_value=True):
            res = client.post("/api/v1/auth/resend-verification", json={
                "email": unverified_user.email
            })

        assert res.status_code == 200
        db.refresh(old_token)
        assert old_token.is_used is True

        new_tokens = db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == unverified_user.id,
            EmailVerificationToken.is_used == False,
        ).all()
        assert len(new_tokens) == 1

    def test_resend_to_nonexistent_email_returns_success(self, client):
        """Anti-enumeration: 200 even for unknown email."""
        res = client.post("/api/v1/auth/resend-verification", json={
            "email": "doesnotexist@example.com"
        })
        assert res.status_code == 200

    def test_resend_to_already_verified_returns_success(self, client, db):
        """Anti-enumeration: 200 even for already-verified user."""
        verified_user = User(
            email="verified@example.com",
            hashed_password=get_password_hash("pass"),
            full_name="Verified",
            is_active=True,
            is_verified=True,
        )
        db.add(verified_user)
        db.commit()

        with patch("api.routes.auth.send_verification_email", return_value=True):
            res = client.post("/api/v1/auth/resend-verification", json={
                "email": "verified@example.com"
            })
        assert res.status_code == 200
