from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


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
