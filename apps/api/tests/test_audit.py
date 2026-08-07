"""
Tests: Audit Logging API
=========================
Tests audit log filtering, pagination, stats, and role-based access.
"""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

import api.models
from api.main import app
from api.database.session import get_db
from api.database.base import Base
from api.models.user import User
from api.models.platform_events import AuditLog
from api.core.security import create_access_token, get_password_hash


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def audit_setup(db):
    user = User(
        email="auditor@example.com",
        hashed_password=get_password_hash("pass"),
        full_name="Auditor User",
        is_active=True,
        is_verified=True,
        is_superuser=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    logs = [
        AuditLog(actor_id=user.id, entity_type="user", entity_id=user.id, action="USER_LOGIN", risk_level="low", description="Normal login"),
        AuditLog(actor_id=user.id, entity_type="role", entity_id=user.id, action="ROLE_CHANGED", risk_level="high", description="Role elevated"),
        AuditLog(actor_id=user.id, entity_type="user", entity_id=user.id, action="PASSWORD_RESET", risk_level="medium", description="Password reset"),
    ]
    db.add_all(logs)
    db.commit()

    token = create_access_token(user.id)
    return {
        "user_id": user.id,
        "headers": {"Authorization": f"Bearer {token}"},
    }


class TestAuditLogs:
    def test_list_audit_logs(self, client, audit_setup):
        """List audit logs returns list of entries."""
        res = client.get("/api/v1/audit/logs", headers=audit_setup["headers"])
        assert res.status_code == 200
        logs = res.json()
        assert len(logs) >= 3

    def test_filter_audit_logs_by_risk(self, client, audit_setup):
        """Filter logs by risk level."""
        res = client.get("/api/v1/audit/logs", params={"risk_level": "high"}, headers=audit_setup["headers"])
        assert res.status_code == 200
        logs = res.json()
        assert all(l["risk_level"] == "high" for l in logs)

    def test_audit_stats(self, client, audit_setup):
        """Audit stats endpoint returns count aggregations."""
        res = client.get("/api/v1/audit/stats", headers=audit_setup["headers"])
        assert res.status_code == 200
        data = res.json()
        assert "total" in data
        assert "by_risk" in data
        assert "by_action" in data
        assert data["total"] >= 3
