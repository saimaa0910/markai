"""
Tests: Account Lifecycle (Deletion & Restore)
================================================
Tests account deletion request, 7-day window, restore, and audit trail.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database.session import get_db
from api.database.base import Base
from api.models.user import User
from api.core.security import get_password_hash, create_access_token


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def active_user(db):
    user = User(
        email="lifecycle@example.com",
        hashed_password=get_password_hash("password123"),
        full_name="Lifecycle User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_headers(active_user):
    token = create_access_token(active_user.id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestAccountDeletion:
    def test_deletion_requires_confirm_true(self, client, auth_headers):
        """Must explicitly set confirm=true."""
        res = client.post("/api/v1/users/me/delete",
            json={"confirm": False},
            headers=auth_headers,
        )
        assert res.status_code == 400
        assert "confirm" in res.json()["detail"].lower()

    def test_deletion_schedules_for_7_days(self, client, db, active_user, auth_headers):
        """Deletion request schedules removal 7 days out."""
        with patch("api.services.email_service.send_account_deletion_scheduled_email", return_value=True):
            res = client.post("/api/v1/users/me/delete",
                json={"confirm": True, "reason": "Testing"},
                headers=auth_headers,
            )
        assert res.status_code == 200
        db.refresh(active_user)

        assert active_user.deletion_requested_at is not None
        assert active_user.scheduled_deletion_at is not None
        assert active_user.is_active is False

    def test_deletion_disables_login(self, client, db, active_user, auth_headers):
        """Account is immediately disabled after deletion request."""
        with patch("api.services.email_service.send_account_deletion_scheduled_email", return_value=True):
            client.post("/api/v1/users/me/delete",
                json={"confirm": True},
                headers=auth_headers,
            )
        db.refresh(active_user)
        assert active_user.is_active is False

    def test_double_deletion_request_fails(self, client, db, active_user, auth_headers):
        """Cannot request deletion twice."""
        active_user.deletion_requested_at = datetime.now(timezone.utc)
        db.commit()

        res = client.post("/api/v1/users/me/delete",
            json={"confirm": True},
            headers=auth_headers,
        )
        assert res.status_code == 400
        assert "already requested" in res.json()["detail"].lower()

    def test_deletion_status_endpoint(self, client, db, active_user, auth_headers):
        """Deletion status returns correct pending state."""
        active_user.deletion_requested_at = datetime.now(timezone.utc)
        active_user.scheduled_deletion_at = datetime.now(timezone.utc) + timedelta(days=5)
        db.commit()

        res = client.get("/api/v1/users/me/deletion-status", headers=auth_headers)
        assert res.status_code == 200
        data = res.json()
        assert data["pending_deletion"] is True
        assert data["days_remaining"] == 4 or data["days_remaining"] == 5
        assert data["can_restore"] is True


class TestAccountRestore:
    def test_restore_cancels_deletion(self, client, db, active_user, auth_headers):
        """Restoring clears deletion fields and re-enables account."""
        active_user.deletion_requested_at = datetime.now(timezone.utc)
        active_user.scheduled_deletion_at = datetime.now(timezone.utc) + timedelta(days=6)
        active_user.is_active = False
        db.commit()

        with patch("api.services.email_service.send_account_restored_email", return_value=True):
            res = client.post("/api/v1/users/me/restore", headers=auth_headers)

        assert res.status_code == 200
        db.refresh(active_user)
        assert active_user.deletion_requested_at is None
        assert active_user.scheduled_deletion_at is None
        assert active_user.is_active is True

    def test_restore_without_pending_deletion_fails(self, client, auth_headers):
        """Restore without active deletion request returns 400."""
        res = client.post("/api/v1/users/me/restore", headers=auth_headers)
        assert res.status_code == 400
        assert "no pending" in res.json()["detail"].lower()

    def test_restore_after_window_fails(self, client, db, active_user, auth_headers):
        """Cannot restore after 7-day window has passed."""
        active_user.deletion_requested_at = datetime.now(timezone.utc) - timedelta(days=8)
        active_user.scheduled_deletion_at = datetime.now(timezone.utc) - timedelta(days=1)
        active_user.is_active = False
        db.commit()

        res = client.post("/api/v1/users/me/restore", headers=auth_headers)
        assert res.status_code == 410

    def test_restore_sends_confirmation_email(self, client, db, active_user, auth_headers):
        """Restoration sends confirmation email."""
        active_user.deletion_requested_at = datetime.now(timezone.utc)
        active_user.scheduled_deletion_at = datetime.now(timezone.utc) + timedelta(days=6)
        active_user.is_active = False
        db.commit()

        with patch("api.services.email_service.send_account_restored_email") as mock_restore:
            client.post("/api/v1/users/me/restore", headers=auth_headers)
            mock_restore.assert_called_once()


class TestAccountCleanupTask:
    def test_cleanup_permanently_deletes_expired_accounts(self, db):
        """Cleanup task deletes accounts past scheduled_deletion_at."""
        from api.tasks.account_cleanup import run_account_cleanup

        expired_user = User(
            email="expired@example.com",
            hashed_password=get_password_hash("pass"),
            full_name="Expired User",
            is_active=False,
            deletion_requested_at=datetime.now(timezone.utc) - timedelta(days=8),
            scheduled_deletion_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add(expired_user)
        db.commit()

        with patch("api.services.email_service.send_account_permanently_deleted_email", return_value=True):
            count = run_account_cleanup(db)

        assert count == 1
        db.refresh(expired_user)
        assert expired_user.email.startswith("deleted_")
        assert expired_user.full_name == "Deleted User"

    def test_cleanup_ignores_active_accounts(self, db, active_user):
        """Cleanup task does NOT touch active accounts."""
        from api.tasks.account_cleanup import run_account_cleanup

        initial_email = active_user.email
        with patch("api.services.email_service.send_account_permanently_deleted_email", return_value=True):
            run_account_cleanup(db)

        db.refresh(active_user)
        assert active_user.email == initial_email

    def test_cleanup_ignores_future_scheduled_deletions(self, db):
        """Cleanup does NOT delete accounts with future scheduled_deletion_at."""
        from api.tasks.account_cleanup import run_account_cleanup

        future_user = User(
            email="future@example.com",
            hashed_password=get_password_hash("pass"),
            full_name="Future User",
            is_active=False,
            deletion_requested_at=datetime.now(timezone.utc),
            scheduled_deletion_at=datetime.now(timezone.utc) + timedelta(days=5),
        )
        db.add(future_user)
        db.commit()

        with patch("api.services.email_service.send_account_permanently_deleted_email", return_value=True):
            count = run_account_cleanup(db)

        assert count == 0
        db.refresh(future_user)
        assert future_user.email == "future@example.com"
