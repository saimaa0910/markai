"""Sprint 8.4 Phase 21: Audit Logging Hardening

Acceptance criteria:
- Audit entries are organization-attributed (via X-Organization-Id header or
  the actor's first membership), so org-scoped audit queries surface auth
  events.
- Failed authentication events are recorded with elevated risk levels.
- Audit logging is best-effort: a write failure must never break the primary
  request being recorded.
"""
import uuid
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from api.models.platform_events import AuditLog
from api.models.membership import UserOrganization, UserRole as MembershipRole
from api.models.organization import Organization
from api.models.user import User
from api.routes.auth import log_audit
from api.core.security import get_password_hash, create_access_token
from api.main import app


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


class _FakeRequest:
    def __init__(self, org_header=None, ip="127.0.0.1", ua="test-agent"):
        self.client = type("Client", (), {"host": ip})()
        self._headers = {}
        if org_header:
            self._headers["x-organization-id"] = org_header
        self._headers["user-agent"] = ua

    @property
    def headers(self):
        return self._headers


def test_log_audit_captures_organization_from_header(db):
    org = Organization(name="Audit Org", slug=f"p21-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.commit()

    user = User(
        email="p21-audit@example.com",
        hashed_password=get_password_hash("pass"),
        full_name="Audit User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()

    req = _FakeRequest(org_header=str(org.id))
    log_audit(db, user.id, "TEST_ACTION", req)

    row = db.execute(
        select(AuditLog).where(AuditLog.action == "TEST_ACTION")
    ).scalar_one()
    assert row.organization_id == org.id
    assert row.actor_id == user.id
    assert row.actor_ip == "127.0.0.1"
    assert row.actor_user_agent == "test-agent"


def test_log_audit_falls_back_to_first_membership(db):
    org = Organization(name="Fallback Org", slug=f"p21b-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()

    user = User(
        email="p21b-audit@example.com",
        hashed_password=get_password_hash("pass"),
        full_name="Audit User B",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    db.add(UserOrganization(user_id=user.id, organization_id=org.id, role=MembershipRole.MEMBER))
    db.commit()

    log_audit(db, user.id, "TEST_ACTION_B", None)

    row = db.execute(
        select(AuditLog).where(AuditLog.action == "TEST_ACTION_B")
    ).scalar_one()
    assert row.organization_id == org.id


def test_log_audit_respects_elevated_risk_level(db):
    user = User(
        email="p21c-audit@example.com",
        hashed_password=get_password_hash("pass"),
        full_name="Audit User C",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.commit()

    log_audit(db, user.id, "USER_LOGIN_FAILED", _FakeRequest(), risk_level="medium")

    row = db.execute(
        select(AuditLog).where(AuditLog.action == "USER_LOGIN_FAILED")
    ).scalar_one()
    assert row.risk_level == "medium"


def test_log_audit_never_raises_on_write_failure():
    broken_db = Mock()
    broken_db.add.side_effect = Exception("database unavailable")

    # Must not raise despite the underlying failure.
    log_audit(broken_db, uuid.uuid4(), "FAILING_ACTION", _FakeRequest())
    broken_db.rollback.assert_called_once()


def test_login_failure_is_logged_with_org_and_medium_risk(db):
    """End-to-end: a failed login produces an org-attributed, medium-risk entry."""
    from api.core.security import get_password_hash
    from api.models.membership import UserOrganization, UserRole as MembershipRole
    from api.models.organization import Organization

    org = Organization(name="Login Org", slug=f"p21d-{uuid.uuid4().hex[:8]}")
    db.add(org)
    db.flush()
    user = User(
        email="p21d-login@example.com",
        hashed_password=get_password_hash("correct-password"),
        full_name="Login User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    db.add(UserOrganization(user_id=user.id, organization_id=org.id, role=MembershipRole.MEMBER))
    db.commit()

    with TestClient(app) as client:
        res = client.post(
            "/api/v1/auth/login",
            json={"username": "p21d-login@example.com", "password": "wrong-password"},
            headers={"X-Organization-Id": str(org.id)},
        )
    assert res.status_code == 401

    row = db.execute(
        select(AuditLog).where(AuditLog.action == "USER_LOGIN_FAILED")
    ).scalar_one()
    assert row.organization_id == org.id
    assert row.risk_level == "medium"
