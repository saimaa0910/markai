from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_prompt_library_version_control():
    """
    Verify Phase 3 prompt version control, history logs, listing aggregates, and delete operations.
    """
    # 1. Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "prompt_editor@example.com",
            "password": "securepassword",
            "full_name": "Prompt Editor",
            "org_name": "Prompt Org",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "prompt_editor@example.com", "password": "securepassword"},
    ).json()
    token = login["access_token"]

    # Retrieve Org details
    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 2. Create Prompt V1
    create_res = client.post(
        "/api/v1/ai/prompts/",
        json={
            "name": "Social Writer",
            "content": "Create a post about {topic}",
            "category": "social",
            "tags": "social,marketing",
            "is_shared": True,
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    prompt_v1 = create_res.json()
    assert prompt_v1["name"] == "Social Writer"
    assert prompt_v1["version"] == 1
    assert prompt_v1["content"] == "Create a post about {topic}"

    # Try creating duplicate v1 prompt (should fail)
    duplicate_res = client.post(
        "/api/v1/ai/prompts/",
        json={"name": "Social Writer", "content": "Different content"},
        headers=headers,
    )
    assert duplicate_res.status_code == 400
    assert "already exists" in duplicate_res.json()["detail"]

    # 3. Update Prompt to V2 (Incrementing version)
    update_res = client.post(
        "/api/v1/ai/prompts/Social Writer/update",
        json={
            "content": "Create an engaging post about {topic} with hashtags",
            "tags": "social,marketing,hashtags",
        },
        headers=headers,
    )
    assert update_res.status_code == 200
    prompt_v2 = update_res.json()
    assert prompt_v2["name"] == "Social Writer"
    assert prompt_v2["version"] == 2
    assert prompt_v2["content"] == "Create an engaging post about {topic} with hashtags"
    assert prompt_v2["tags"] == "social,marketing,hashtags"
    # Category falls back to the previous version
    assert prompt_v2["category"] == "social"

    # 4. List Prompts (should return only the latest version of the prompt)
    list_res = client.get("/api/v1/ai/prompts/", headers=headers)
    assert list_res.status_code == 200
    prompts_list = list_res.json()
    assert len(prompts_list) == 1
    assert prompts_list[0]["version"] == 2

    # 5. Get latest prompt by name
    get_res = client.get("/api/v1/ai/prompts/Social Writer", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["version"] == 2

    # 6. Retrieve Prompt History (should return all historical records, ordered desc)
    history_res = client.get("/api/v1/ai/prompts/Social Writer/history", headers=headers)
    assert history_res.status_code == 200
    history = history_res.json()
    assert len(history) == 2
    assert history[0]["version"] == 2
    assert history[1]["version"] == 1

    # 7. Delete Prompt Family
    delete_res = client.delete("/api/v1/ai/prompts/Social Writer", headers=headers)
    assert delete_res.status_code == 204

    # Verify everything is deleted
    list_after = client.get("/api/v1/ai/prompts/", headers=headers).json()
    assert len(list_after) == 0
