from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_content_generator_and_ab_testing():
    """
    Verify Content Generator endpoint produces multiple variants,
    supports rating updates, and maintains multi-tenant isolation.
    """
    # 1. Register and login User A (creates Org A)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a_gen@example.com",
            "password": "superpassword123",
            "full_name": "User A Gen",
            "org_name": "Org A Gen",
        },
    )
    login_a = client.post(
        "/api/v1/auth/login",
        data={"username": "user_a_gen@example.com", "password": "superpassword123"},
    ).json()
    token_a = login_a["access_token"]

    # Retrieve Org A details
    orgs_a = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_a}"},
    ).json()
    org_a_id = orgs_a[0]["id"]

    # 2. Register and login User B (creates Org B)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_b_gen@example.com",
            "password": "superpassword123",
            "full_name": "User B Gen",
            "org_name": "Org B Gen",
        },
    )
    login_b = client.post(
        "/api/v1/auth/login",
        data={"username": "user_b_gen@example.com", "password": "superpassword123"},
    ).json()
    token_b = login_b["access_token"]

    # Retrieve Org B details
    orgs_b = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    org_b_id = orgs_b[0]["id"]

    # 3. Request multi-variant copy generation under Org A
    gen_res = client.post(
        "/api/v1/generator/",
        json={
            "title": "Email variant campaign",
            "copy_type": "email",
            "topic": "Antigravity SaaS Platform launch",
            "tone": "creative",
            "audience": "Developers",
            "keywords": "AI, agents, speed",
        },
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert gen_res.status_code == 201
    gen_data = gen_res.json()
    assert gen_data["title"] == "Email variant campaign"
    assert len(gen_data["variants"]) == 2
    assert gen_data["variants"][0]["variant_label"] == "Variant A"
    assert gen_data["variants"][1]["variant_label"] == "Variant B"

    # 4. Try listing generated copies under Org B (should be isolated/empty)
    list_b = client.get(
        "/api/v1/generator/",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    ).json()
    assert len(list_b) == 0

    # 5. Rate Variant A using Org A token
    variant_a_id = gen_data["variants"][0]["id"]
    rate_res = client.post(
        f"/api/v1/generator/variants/{variant_a_id}/rate",
        json={"rating": 5},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert rate_res.status_code == 200
    assert rate_res.json()["rating"] == 5

    # 6. Try rating Variant A using Org B token (should fail with 404 block to prevent cross-tenant tampering)
    rate_blocked = client.post(
        f"/api/v1/generator/variants/{variant_a_id}/rate",
        json={"rating": 1},
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert rate_blocked.status_code == 404
