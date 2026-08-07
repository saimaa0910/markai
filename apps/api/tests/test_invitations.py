"""
Tests: Organization Invitations
=================================
Tests creating, listing, accepting, rejecting, resending, and revoking invitations.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.database.session import get_db
from api.database.base import Base
from api.models.user import User
from api.models.organization import Organization
from api.models.membership import UserOrganization, OrganizationInvitation, UserRole
from api.core.security import create_access_token, get_password_hash


@pytest.fixture(scope="function")
def db(db_session):
    yield db_session


@pytest.fixture
def client(db):
    with TestClient(app) as c:
        yield c


@pytest.fixture
def invite_setup(db):
    org = Organization(name="Invite Corp", slug="invite-corp")
    db.add(org)
    db.flush()

    owner = User(
        email="owner@invite.com",
        hashed_password=get_password_hash("pass"),
        full_name="Invite Owner",
        is_active=True,
        is_verified=True,
    )
    invitee = User(
        email="invitee@invite.com",
        hashed_password=get_password_hash("pass"),
        full_name="Invited User",
        is_active=True,
        is_verified=True,
    )
    db.add_all([owner, invitee])
    db.flush()

    db.add(UserOrganization(user_id=owner.id, organization_id=org.id, role=UserRole.OWNER))
    db.commit()

    return {
        "org": org,
        "owner": owner,
        "invitee": invitee,
        "owner_headers": {
            "Authorization": f"Bearer {create_access_token(owner.id)}",
            "X-Organization-Id": str(org.id),
        },
        "invitee_headers": {
            "Authorization": f"Bearer {create_access_token(invitee.id)}",
        },
    }


class TestInvitations:
    def test_create_invitation(self, client, invite_setup):
        """Owner can send invitation to email."""
        with patch("api.routes.organizations.send_invitation_email", return_value=True):
            res = client.post(
                f"/api/v1/organizations/{invite_setup['org'].id}/invitations/",
                json={"email": "newinvite@example.com", "role": "MEMBER"},
                headers=invite_setup["owner_headers"],
            )
        assert res.status_code == 200
        data = res.json()
        assert data["email"] == "newinvite@example.com"
        assert "invite_link" in data

    def test_list_invitations(self, client, invite_setup):
        """List active pending invitations."""
        with patch("api.routes.organizations.send_invitation_email", return_value=True):
            client.post(
                f"/api/v1/organizations/{invite_setup['org'].id}/invitations/",
                json={"email": "listinvite@example.com", "role": "MEMBER"},
                headers=invite_setup["owner_headers"],
            )

        res = client.get(
            f"/api/v1/organizations/{invite_setup['org'].id}/invitations/",
            headers=invite_setup["owner_headers"],
        )
        assert res.status_code == 200
        assert len(res.json()) >= 1

    def test_accept_invitation(self, client, db, invite_setup):
        """Invited user can accept invitation."""
        with patch("api.routes.organizations.send_invitation_email", return_value=True):
            inv_res = client.post(
                f"/api/v1/organizations/{invite_setup['org'].id}/invitations/",
                json={"email": invite_setup["invitee"].email, "role": "MEMBER"},
                headers=invite_setup["owner_headers"],
            )
        inv_id = inv_res.json()["id"]

        res = client.post(
            f"/api/v1/organizations/invitations/{inv_id}/accept/",
            headers=invite_setup["invitee_headers"],
        )
        assert res.status_code == 200
        assert res.json()["success"] is True

        m = db.query(UserOrganization).filter(
            UserOrganization.user_id == invite_setup["invitee"].id,
            UserOrganization.organization_id == invite_setup["org"].id,
        ).first()
        assert m is not None

    def test_resend_invitation(self, client, invite_setup):
        """Owner can resend pending invitation."""
        with patch("api.routes.organizations.send_invitation_email", return_value=True):
            inv_res = client.post(
                f"/api/v1/organizations/{invite_setup['org'].id}/invitations/",
                json={"email": "resendtest@example.com", "role": "MEMBER"},
                headers=invite_setup["owner_headers"],
            )
            inv_id = inv_res.json()["id"]

            res = client.post(
                f"/api/v1/organizations/{invite_setup['org'].id}/invitations/{inv_id}/resend",
                headers=invite_setup["owner_headers"],
            )
        assert res.status_code == 200
        assert res.json()["resent_count"] >= 1

    def test_revoke_invitation(self, client, invite_setup):
        """Owner can revoke invitation."""
        with patch("api.routes.organizations.send_invitation_email", return_value=True):
            inv_res = client.post(
                f"/api/v1/organizations/{invite_setup['org'].id}/invitations/",
                json={"email": "revoketest@example.com", "role": "MEMBER"},
                headers=invite_setup["owner_headers"],
            )
            inv_id = inv_res.json()["id"]

        res = client.delete(
            f"/api/v1/organizations/{invite_setup['org'].id}/invitations/{inv_id}",
            headers=invite_setup["owner_headers"],
        )
        assert res.status_code == 200
        assert res.json()["success"] is True
