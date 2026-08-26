"""Sprint 8.4 Phase 20: RBAC Hardening

Acceptance criteria: role assignment/revocation is strictly bound to the
caller's organization context, the system OWNER role is owner-only, and an
organization can never be left ownerless.

Covers:
- ADMIN cannot assign a role into another organization (cross-org escalation).
- ADMIN cannot grant the system OWNER role; only the org OWNER can.
- ADMIN cannot revoke the system OWNER role.
- Target user must already be a member of the org.
- The last OWNER of an org cannot be demoted.
"""
import uuid

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.core.security import create_access_token, get_password_hash
from api.models.auth import Role
from api.models.iam import UserRole
from api.models.membership import UserOrganization, UserRole as MembershipRole
from api.models.organization import Organization
from api.models.user import User


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


def _user(db, email) -> User:
    user = User(
        email=email,
        hashed_password=get_password_hash("pass"),
        full_name="RBAC User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    db.flush()
    return user


@pytest.fixture
def org_setup(db):
    org_a = Organization(name="Org A", slug=f"p20-a-{uuid.uuid4().hex[:8]}")
    org_b = Organization(name="Org B", slug=f"p20-b-{uuid.uuid4().hex[:8]}")
    db.add_all([org_a, org_b])
    db.flush()

    owner = _user(db, "p20-owner@example.com")
    admin = _user(db, "p20-admin@example.com")
    member = _user(db, "p20-member@example.com")
    outsider = _user(db, "p20-outsider@example.com")

    db.add(UserOrganization(user_id=owner.id, organization_id=org_a.id, role=MembershipRole.OWNER))
    db.add(UserOrganization(user_id=admin.id, organization_id=org_a.id, role=MembershipRole.ADMIN))
    db.add(UserOrganization(user_id=member.id, organization_id=org_a.id, role=MembershipRole.MEMBER))
    db.add(UserOrganization(user_id=admin.id, organization_id=org_b.id, role=MembershipRole.ADMIN))
    db.commit()

    return {
        "org_a": org_a,
        "org_b": org_b,
        "owner": owner,
        "admin": admin,
        "member": member,
        "outsider": outsider,
        "owner_token": create_access_token(owner.id),
        "admin_token": create_access_token(admin.id),
    }


def _headers(token: str, org_id: uuid.UUID) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "X-Organization-Id": str(org_id),
    }


def _system_role(db, name: str) -> Role:
    role = Role(name=name, display_name=name, is_system=True)
    db.add(role)
    db.commit()
    return role


class TestAssignRole:
    def test_owner_can_assign_member_role(self, client, db, org_setup):
        role = Role(name="ANALYST", display_name="Analyst", is_system=False)
        db.add(role)
        db.commit()

        res = client.post(
            f"/api/v1/rbac/users/{org_setup['member'].id}/roles",
            json={"role_id": str(role.id), "organization_id": str(org_setup["org_a"].id)},
            headers=_headers(org_setup["owner_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 201

    def test_cross_org_assignment_blocked(self, client, db, org_setup):
        role = Role(name="SNEAKY", display_name="Sneaky", is_system=False)
        db.add(role)
        db.commit()

        res = client.post(
            f"/api/v1/rbac/users/{org_setup['member'].id}/roles",
            json={"role_id": str(role.id), "organization_id": str(org_setup["org_b"].id)},
            headers=_headers(org_setup["admin_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 403

    def test_admin_cannot_grant_owner_role(self, client, db, org_setup):
        owner_role = _system_role(db, "OWNER")

        res = client.post(
            f"/api/v1/rbac/users/{org_setup['admin'].id}/roles",
            json={"role_id": str(owner_role.id), "organization_id": str(org_setup["org_a"].id)},
            headers=_headers(org_setup["admin_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 403

    def test_owner_can_grant_owner_role(self, client, db, org_setup):
        owner_role = _system_role(db, "OWNER")

        res = client.post(
            f"/api/v1/rbac/users/{org_setup['admin'].id}/roles",
            json={"role_id": str(owner_role.id), "organization_id": str(org_setup["org_a"].id)},
            headers=_headers(org_setup["owner_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 201

    def test_target_must_be_member(self, client, db, org_setup):
        role = Role(name="GUEST_ROLE", display_name="Guest", is_system=False)
        db.add(role)
        db.commit()

        res = client.post(
            f"/api/v1/rbac/users/{org_setup['outsider'].id}/roles",
            json={"role_id": str(role.id), "organization_id": str(org_setup["org_a"].id)},
            headers=_headers(org_setup["owner_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 400


class TestRemoveRole:
    def test_admin_cannot_revoke_owner_role(self, client, db, org_setup):
        owner_role = _system_role(db, "OWNER")
        db.add(UserRole(
            user_id=org_setup["admin"].id,
            role_id=owner_role.id,
            organization_id=org_setup["org_a"].id,
            granted_by=org_setup["owner"].id,
        ))
        db.commit()

        res = client.delete(
            f"/api/v1/rbac/users/{org_setup['admin'].id}/roles/{owner_role.id}",
            headers=_headers(org_setup["admin_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 403

    def test_owner_cannot_demote_last_owner(self, client, db, org_setup):
        owner_role = _system_role(db, "OWNER")
        db.add(UserRole(
            user_id=org_setup["owner"].id,
            role_id=owner_role.id,
            organization_id=org_setup["org_a"].id,
            granted_by=org_setup["owner"].id,
        ))
        db.commit()

        res = client.delete(
            f"/api/v1/rbac/users/{org_setup['owner'].id}/roles/{owner_role.id}",
            headers=_headers(org_setup["owner_token"], org_setup["org_a"].id),
        )
        assert res.status_code == 409
