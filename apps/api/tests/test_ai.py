from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_ai_platform_and_gateway():
    """
    Verify AI Platform features: Prompts library, conversation sessions,
    LLM Gateway provider routing, and multi-tenant security isolation.
    """
    # 1. Register and login User A (creates Org A)
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "user_a_ai@example.com",
            "password": "superpassword123",
            "full_name": "User A AI",
            "org_name": "Org A AI",
        },
    )
    login_a = client.post(
        "/api/v1/auth/login",
        data={"username": "user_a_ai@example.com", "password": "superpassword123"},
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
            "email": "user_b_ai@example.com",
            "password": "superpassword123",
            "full_name": "User B AI",
            "org_name": "Org B AI",
        },
    )
    login_b = client.post(
        "/api/v1/auth/login",
        data={"username": "user_b_ai@example.com", "password": "superpassword123"},
    ).json()
    token_b = login_b["access_token"]

    # Retrieve Org B details
    orgs_b = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token_b}"},
    ).json()
    org_b_id = orgs_b[0]["id"]

    # 3. Create Prompt Template under Org A
    prompt_a_res = client.post(
        "/api/v1/ai/prompts/",
        json={"name": "Ad Writer", "content": "Write high-converting ads for: {topic}"},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert prompt_a_res.status_code == 201
    prompt_a = prompt_a_res.json()
    assert prompt_a["name"] == "Ad Writer"
    assert prompt_a["organization_id"] == org_a_id

    # 4. Check prompt listing under Org B (should be isolated/empty)
    prompts_b_res = client.get(
        "/api/v1/ai/prompts/",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert prompts_b_res.status_code == 200
    assert len(prompts_b_res.json()) == 0

    # 5. Create Conversation under Org A
    conv_a_res = client.post(
        "/api/v1/ai/conversations/",
        json={"title": "Ad Writing Campaign"},
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert conv_a_res.status_code == 201
    conv_a = conv_a_res.json()
    assert conv_a["title"] == "Ad Writing Campaign"
    assert conv_a["organization_id"] == org_a_id

    # 6. Post User message applying Prompt Template, trigger LLM Gateway routing response
    msg_res = client.post(
        f"/api/v1/ai/conversations/{conv_a['id']}/messages",
        json={
            "content": "SaaS Platform",
            "model_name": "gemini-1.5-flash",
            "prompt_id": prompt_a["id"],
        },
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    
    # Assert assistant response contains simulation signature and routed model
    assert msg_data["role"] == "assistant"
    assert "Gemini Router (gemini-1.5-flash)" in msg_data["content"]
    assert "Ad Writer" in msg_data["content"] or "Write high-converting ads for: {topic}" in msg_data["content"]

    # 7. Check message logs for Conversation A under Org A (must contain 2 messages: user & assistant)
    history_res = client.get(
        f"/api/v1/ai/conversations/{conv_a['id']}/messages",
        headers={"Authorization": f"Bearer {token_a}", "X-Organization-ID": org_a_id},
    )
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"

    # 8. User B tries to view Conversation A messages (should return 404 Not Found to prevent data leakage)
    blocked_history = client.get(
        f"/api/v1/ai/conversations/{conv_a['id']}/messages",
        headers={"Authorization": f"Bearer {token_b}", "X-Organization-ID": org_b_id},
    )
    assert blocked_history.status_code == 404
