"""
Tests: Enterprise RBAC System
===============================
Tests roles, permissions, RBAC middleware, custom roles, and permission checks.
"""
import uuid
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database.session import get_db
from api.database.base import Base
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, UserRole as EnumUserRole
from api.models.auth import Role, Permission
from api.models.iam import UserRole
from api.core.security import create_access_token, get_password_hash


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def org_setup(db):
    org = Organization(name="RBAC Corp", slug="rbac-corp")
    db.add(org)
    db.flush()

    owner = User(
        email="owner@rbac.com",
        hashed_password=get_password_hash("pass"),
        full_name="Org Owner",
        is_active=True,
        is_verified=True,
    )
    member = User(
        email="member@rbac.com",
        hashed_password=get_password_hash("pass"),
        full_name="Org Member",
        is_active=True,
        is_verified=True,
    )
    db.add_all([owner, member])
    db.flush()

    db.add(UserOrganization(user_id=owner.id, organization_id=org.id, role=EnumUserRole.OWNER))
    db.add(UserOrganization(user_id=member.id, organization_id=org.id, role=EnumUserRole.MEMBER))
    db.commit()

    return {
        "org": org,
        "owner": owner,
        "member": member,
        "owner_token": create_access_token(owner.id),
        "member_token": create_access_token(member.id),
    }


class TestRBACRoutes:
    def test_list_roles(self, client, org_setup):
        """List system and custom roles."""
        headers = {
            "Authorization": f"Bearer {org_setup['owner_token']}",
            "X-Organization-Id": str(org_setup["org"].id),
        }
        res = client.get("/api/v1/rbac/roles", headers=headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_create_custom_role(self, client, org_setup):
        """Org owner can create custom role."""
        headers = {
            "Authorization": f"Bearer {org_setup['owner_token']}",
            "X-Organization-Id": str(org_setup["org"].id),
        }
        res = client.post("/api/v1/rbac/roles",
            json={"name": "CONTENT_CREATOR", "display_name": "Content Creator"},
            headers=headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["name"] == "CONTENT_CREATOR"
        assert data["is_system"] is False

    def test_member_cannot_create_custom_role(self, client, org_setup):
        """Regular member cannot create custom roles."""
        headers = {
            "Authorization": f"Bearer {org_setup['member_token']}",
            "X-Organization-Id": str(org_setup["org"].id),
        }
        res = client.post("/api/v1/rbac/roles",
            json={"name": "UNAUTHORIZED_ROLE"},
            headers=headers,
        )
        assert res.status_code == 403

    def test_assign_role_to_user(self, client, db, org_setup):
        """Owner can assign role to member."""
        headers = {
            "Authorization": f"Bearer {org_setup['owner_token']}",
            "X-Organization-Id": str(org_setup["org"].id),
        }

        role = Role(name="ANALYST", display_name="Analyst", is_system=False)
        db.add(role)
        db.commit()

        res = client.post(f"/api/v1/rbac/users/{org_setup['member'].id}/roles",
            json={
                "role_id": str(role.id),
                "organization_id": str(org_setup["org"].id),
            },
            headers=headers,
        )
        assert res.status_code == 201

        perm_res = client.get(
            f"/api/v1/rbac/users/{org_setup['member'].id}/permissions",
            params={"organization_id": str(org_setup["org"].id)},
            headers={"Authorization": f"Bearer {org_setup['member_token']}"},
        )
        assert perm_res.status_code == 200
        roles_assigned = [r["name"] for r in perm_res.json()["roles"]]
        assert "ANALYST" in roles_assigned
