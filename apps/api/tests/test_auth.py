from fastapi.testclient import TestClient
from api.main import app
import uuid

client = TestClient(app)


def _register_and_login(email: str, password: str = "superpassword123"):
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Auth Test User",
            "org_name": f"Auth Test Org {uuid.uuid4()}",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    return login_response.json()


def test_user_registration_and_login():
    """
    Test user registration, automated organization creation, and token login.
    """
    email = "testuser@example.com"
    password = "superpassword123"
    full_name = "Test User"
    org_name = "Test Enterprise Org"

    # 1. Register User
    reg_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": full_name,
            "org_name": org_name,
        },
    )
    assert reg_response.status_code == 201
    assert reg_response.json()["email"] == email
    assert reg_response.json()["full_name"] == full_name

    # 2. Login User
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    tokens = login_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"

    # 3. Retrieve user profile details using token
    profile_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert profile_response.status_code == 200
    assert profile_response.json()["email"] == email

    # 4. Retrieve organizations user belongs to
    orgs_response = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert orgs_response.status_code == 200
    orgs = orgs_response.json()
    assert len(orgs) == 1
    assert orgs[0]["name"] == org_name
    assert orgs[0]["slug"] == "test-enterprise-org"


def test_token_refresh():
    """
    Test that users can rotate access and refresh tokens.
    """
    email = "refreshuser@example.com"
    password = "superpassword123"

    # 1. Register & Login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": password,
            "full_name": "Refresh User",
            "org_name": "Refresh Org",
        },
    )
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    tokens = login_response.json()

    # 2. Refresh Token
    refresh_response = client.post(
        f"/api/v1/auth/refresh?refresh_token={tokens['refresh_token']}"
    )
    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens


def test_password_hashing_uses_argon2_and_verifies_legacy_bcrypt():
    from api.core.security import get_password_hash, verify_password

    hashed = get_password_hash("superpassword123")

    assert hashed.startswith("$argon2")
    assert verify_password("superpassword123", hashed)
    assert not verify_password("wrongpassword", hashed)
    import bcrypt

    legacy_hash = bcrypt.hashpw(b"legacy-password", bcrypt.gensalt()).decode("utf-8")
    assert verify_password("legacy-password", legacy_hash)


def test_session_revocation_invalidates_access_token():
    email = f"session-{uuid.uuid4()}@example.com"
    tokens = _register_and_login(email)

    sessions_response = client.get(
        "/api/v1/sessions/",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert sessions_response.status_code == 200
    current_session = next(s for s in sessions_response.json() if s["is_current"])

    revoke_response = client.request(
        "DELETE",
        f"/api/v1/sessions/{current_session['id']}",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"reason": "test_revocation"},
    )
    assert revoke_response.status_code == 200

    profile_response = client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert profile_response.status_code == 401


def test_invitation_creation_accepts_json_body_and_sends_email(monkeypatch):
    sent = {}

    def fake_send_invitation_email(to_email, inviter_name, org_name, role, accept_url):
        sent.update(
            {
                "to_email": to_email,
                "inviter_name": inviter_name,
                "org_name": org_name,
                "role": role,
                "accept_url": accept_url,
            }
        )
        return True

    monkeypatch.setattr(
        "api.routes.organizations.send_invitation_email",
        fake_send_invitation_email,
    )

    email = f"owner-{uuid.uuid4()}@example.com"
    tokens = _register_and_login(email)
    orgs_response = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    org_id = orgs_response.json()[0]["id"]

    invitee = f"invitee-{uuid.uuid4()}@example.com"
    invite_response = client.post(
        f"/api/v1/organizations/{org_id}/invitations/",
        headers={
            "Authorization": f"Bearer {tokens['access_token']}",
            "X-Organization-ID": org_id,
        },
        json={"email": invitee, "role": "MEMBER"},
    )

    assert invite_response.status_code == 200
    assert invite_response.json()["email"] == invitee
    assert sent["to_email"] == invitee
    assert "/auth/accept-invitation?token=" in sent["accept_url"]


def test_change_email_static_route_and_confirm_body(monkeypatch):
    verify_links = []

    def fake_send_change_email_verification(to_email, full_name, verify_url):
        verify_links.append(verify_url)
        return True

    monkeypatch.setattr(
        "api.services.email_service.send_change_email_verification",
        fake_send_change_email_verification,
    )

    password = "superpassword123"
    email = f"email-change-{uuid.uuid4()}@example.com"
    tokens = _register_and_login(email, password)
    new_email = f"email-change-new-{uuid.uuid4()}@example.com"

    change_response = client.patch(
        "/api/v1/users/email",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
        json={"new_email": new_email, "password": password},
    )
    assert change_response.status_code == 200
    assert verify_links

    from urllib.parse import parse_qs, urlparse

    query = parse_qs(urlparse(verify_links[0]).query)
    token = query["token"][0]
    confirm_response = client.post(
        "/api/v1/users/email/confirm",
        json={"token": token, "new_email": new_email},
    )
    assert confirm_response.status_code == 200


def test_mfa_login_enforcement_and_verification(monkeypatch, db_session):
    """
    Test that users with MFA enabled are prompted for MFA and can verify successfully.
    """
    import pyotp
    from api.models.user import User

    email = f"mfa-user-{uuid.uuid4()}@example.com"
    password = "superpassword123"

    # 1. Register & Login
    _register_and_login(email, password)

    # 2. Get user database object to set up MFA secret
    db = db_session
    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    # Manually enable MFA for test
    secret = pyotp.random_base32()
    user.mfa_secret = secret
    user.mfa_enabled = True
    user.mfa_method = "totp"
    db.add(user)
    db.commit()

    # 3. Login again — should require MFA
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data.get("mfa_required") is True
    mfa_token = login_data.get("mfa_token")
    assert mfa_token is not None

    # 4. Try verifying with wrong code
    verify_response = client.post(
        "/api/v1/auth/mfa/login",
        json={"mfa_token": mfa_token, "code": "000000"},
    )
    assert verify_response.status_code == 400

    # 5. Verify with correct code
    totp = pyotp.TOTP(secret)
    correct_code = totp.now()

    verify_response = client.post(
        "/api/v1/auth/mfa/login",
        json={"mfa_token": mfa_token, "code": correct_code},
    )
    assert verify_response.status_code == 200
    tokens = verify_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


def test_oauth_mock_bypass_and_invitation(db_session):
    """
    Test that the backend OAuth mock token bypass provisions users correctly
    and handles organization invitation linking.
    """
    from api.models.user import User
    from api.models.membership import UserOrganization, OrganizationInvitation, UserRole
    from api.models.organization import Organization
    from datetime import datetime, timedelta, timezone

    # 1. Standard mock OAuth login
    mock_token = f"mock_google_user_{uuid.uuid4().hex[:6]}"
    oauth_response = client.post(
        "/api/v1/auth/oauth/google",
        json={"provider": "google", "access_token": mock_token},
    )
    assert oauth_response.status_code == 200
    tokens = oauth_response.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens

    # Verify user and default org were created
    db = db_session
    user = db.query(User).filter(User.email == f"{mock_token.replace('mock_', '')}@example.com").first()
    assert user is not None
    assert user.is_verified is True

    orgs_membership = db.query(UserOrganization).filter(UserOrganization.user_id == user.id).all()
    assert len(orgs_membership) == 1
    assert orgs_membership[0].role == UserRole.OWNER

    # 2. OAuth login with invitation token
    org_id = None
    # Create an org and invite
    org = Organization(name="Invited Org", slug=f"invited-org-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.flush()
    org_id = org.id

    invite_token = f"invite-token-{uuid.uuid4().hex}"
    invitation = OrganizationInvitation(
        email=f"invited-oauth-{uuid.uuid4().hex[:6]}@example.com",
        organization_id=org.id,
        role=UserRole.MEMBER,
        token=invite_token,
        expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    db.add(invitation)
    db.commit()

    # Login via mock OAuth with invitation token
    invited_mock_token = f"mock_google_invited_{uuid.uuid4().hex[:6]}"
    invited_email = f"{invited_mock_token.replace('mock_', '')}@example.com"
    inv = db.query(OrganizationInvitation).filter(OrganizationInvitation.token == invite_token).first()
    inv.email = invited_email
    db.add(inv)
    db.commit()

    oauth_invite_response = client.post(
        "/api/v1/auth/oauth/google",
        json={"provider": "google", "access_token": invited_mock_token, "invitation_token": invite_token},
    )
    assert oauth_invite_response.status_code == 200

    # Verify user joined the invited organization and did NOT get a new one
    invited_user = db.query(User).filter(User.email == invited_email).first()
    assert invited_user is not None

    memberships = db.query(UserOrganization).filter(UserOrganization.user_id == invited_user.id).all()
    assert len(memberships) == 1
    assert memberships[0].organization_id == org_id
    assert memberships[0].role == UserRole.MEMBER

    # Verify invitation is marked accepted
    inv = db.query(OrganizationInvitation).filter(OrganizationInvitation.token == invite_token).first()
    assert inv.is_accepted is True
