import uuid
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from api.main import app
from api.models.user import User
from api.models.membership import UserOrganization, UserRole, OrganizationInvitation

client = TestClient(app)


def test_phase2_forgot_reset_password(db_session) -> None:
    # 1. Create a user
    email = "forgot@example.com"
    client.post("/api/v1/auth/register", json={
        "email": email,
        "full_name": "Forgot User",
        "password": "Password123!",
        "org_name": "Forgot Org"
    })
    
    # 2. Call forgot password
    res = client.post(f"/api/v1/auth/forgot-password?email={email}")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 3. Get the user's ID
    user = db_session.query(User).filter(User.email == email).first()
    assert user is not None
    
    # Generate token
    from api.core.security import create_access_token
    token = create_access_token(user.id, expires_delta=timedelta(hours=1))

    # 4. Call reset-password
    res = client.post(f"/api/v1/auth/reset-password?token={token}&new_password=NewPassword123!")
    assert res.status_code == 200
    assert res.json()["success"] is True

    # 5. Verify user can login with new password
    res = client.post("/api/v1/auth/login", data={
        "username": email,
        "password": "NewPassword123!"
    })
    assert res.status_code == 200


def test_phase2_organization_management_and_invitations(db_session) -> None:
    # 1. Register owner user
    owner_email = "owner@example.com"
    reg_res = client.post("/api/v1/auth/register", json={
        "email": owner_email,
        "full_name": "Owner User",
        "password": "Password123!",
        "org_name": "Owner Org"
    })
    assert reg_res.status_code == 201
    
    # Login as owner
    login_res = client.post("/api/v1/auth/login", data={
        "username": owner_email,
        "password": "Password123!"
    })
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get active organization
    user = db_session.query(User).filter(User.email == owner_email).first()
    assert user is not None
    membership = db_session.query(UserOrganization).filter(UserOrganization.user_id == user.id).first()
    assert membership is not None
    org_id = membership.organization_id
    headers["X-Organization-ID"] = str(org_id)

    # 2. Invite a new member
    invite_email = "invited@example.com"
    invite_res = client.post(
        f"/api/v1/organizations/{org_id}/invitations/?email={invite_email}&role=MEMBER",
        headers=headers
    )
    assert invite_res.status_code == 200
    assert invite_res.json()["email"] == invite_email
    
    # Get the token
    invitation = db_session.query(OrganizationInvitation).filter(OrganizationInvitation.email == invite_email).first()
    assert invitation is not None
    assert invitation.is_accepted is False
    token_str = invitation.token
    
    # 3. Accept invitation via registration flow
    reg_invited_res = client.post("/api/v1/auth/register", json={
        "email": invite_email,
        "full_name": "Invited User",
        "password": "Password123!",
        "invitation_token": token_str
    })
    assert reg_invited_res.status_code == 201
    
    # Verify the invitation status & membership in DB
    db_session.refresh(invitation)
    assert invitation.is_accepted is True
    
    invited_user = db_session.query(User).filter(User.email == invite_email).first()
    assert invited_user is not None
    invited_membership = db_session.query(UserOrganization).filter(
        UserOrganization.user_id == invited_user.id,
        UserOrganization.organization_id == org_id
    ).first()
    assert invited_membership is not None
    assert invited_membership.role == UserRole.MEMBER
