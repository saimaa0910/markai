import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_standard_prompts_v1_endpoints_e2e():
    # 1. Register and login test user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "prompt_v1_user@enterprise.com",
            "password": "Password123!",
            "full_name": "Prompt Tester",
            "org_name": "Standard Prompts Org"
        }
    )
    assert reg_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "prompt_v1_user@enterprise.com", "password": "Password123!"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Get Organization ID
    org_res = client.get("/api/v1/organizations/", headers=headers)
    assert org_res.status_code == 200
    org_id = org_res.json()[0]["id"]
    headers["X-Organization-ID"] = org_id

    # 3. Create Categories
    cat_res = client.post(
        "/api/v1/prompts/categories",
        json={"name": "Engineering", "description": "Dev prompts", "color": "#0052CC", "icon": "code"},
        headers=headers
    )
    assert cat_res.status_code in [200, 201]
    cat_id = cat_res.json()["id"]

    list_cat_res = client.get("/api/v1/prompts/categories", headers=headers)
    assert list_cat_res.status_code == 200
    assert len(list_cat_res.json()) >= 1

    # 4. Create Tags
    tag_res = client.post(
        "/api/v1/prompts/tags",
        json={"name": "python", "color": "#3572A5"},
        headers=headers
    )
    assert tag_res.status_code in [200, 201]

    list_tag_res = client.get("/api/v1/prompts/tags", headers=headers)
    assert list_tag_res.status_code == 200
    assert len(list_tag_res.json()) >= 1

    # 5. Create Collection & Folder
    col_res = client.post(
        "/api/v1/prompts/collections",
        json={"name": "Dev Operations", "description": "DevOps prompt collection"},
        headers=headers
    )
    assert col_res.status_code in [200, 201]
    col_id = col_res.json()["id"]

    folder_res = client.post(
        "/api/v1/prompts/folders",
        json={"name": "CI/CD Pipeline", "collection_id": col_id},
        headers=headers
    )
    assert folder_res.status_code in [200, 201]
    folder_id = folder_res.json()["id"]

    # 6. Create Prompt via REST /api/v1/prompts
    prompt_create_res = client.post(
        "/api/v1/prompts/",
        json={
            "name": "GitHub Actions Builder",
            "content": "Create a GitHub Actions workflow for {{language}} application with {{framework}} support.",
            "category_id": cat_id,
            "folder_id": folder_id,
            "collection_id": col_id,
            "tags": ["ci-cd", "automation"],
            "visibility": "organization"
        },
        headers=headers
    )
    assert prompt_create_res.status_code == 201
    prompt_data = prompt_create_res.json()
    prompt_id = prompt_data["id"]

    # 7. List Prompts
    list_prompts_res = client.get("/api/v1/prompts/", headers=headers)
    assert list_prompts_res.status_code == 200
    data = list_prompts_res.json()
    items = data["items"] if isinstance(data, dict) and "items" in data else data
    assert len(items) >= 1

    # 8. Get Prompt by ID
    get_p_res = client.get(f"/api/v1/prompts/{prompt_id}", headers=headers)
    assert get_p_res.status_code == 200
    assert get_p_res.json()["name"] == "GitHub Actions Builder"

    # 9. Update Prompt
    update_res = client.put(
        f"/api/v1/prompts/{prompt_id}",
        json={
            "content": "Updated GH Actions workflow template for {{language}} and {{framework}} with caching.",
            "change_log": "Added dependency caching"
        },
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["version"] == 2

    # 10. Favorite, Pin, Archive
    fav_res = client.post(f"/api/v1/prompts/{prompt_id}/favorite", headers=headers)
    assert fav_res.status_code == 200
    assert fav_res.json()["is_favorite"] is True

    pin_res = client.post(f"/api/v1/prompts/{prompt_id}/pin", headers=headers)
    assert pin_res.status_code == 200
    assert pin_res.json()["is_pinned"] is True

    arch_res = client.post(f"/api/v1/prompts/{prompt_id}/archive", headers=headers)
    assert arch_res.status_code == 200
    assert arch_res.json()["is_archived"] is True

    # 11. Clone Prompt
    clone_res = client.post(
        f"/api/v1/prompts/{prompt_id}/clone",
        json={"new_name": "GitHub Actions Builder Copy"},
        headers=headers
    )
    assert clone_res.status_code == 201
    cloned_id = clone_res.json()["id"]

    # 12. Search Prompts REST
    search_res = client.post(
        "/api/v1/prompts/search",
        json={"query": "GitHub", "is_archived": True},
        headers=headers
    )
    assert search_res.status_code == 200
    s_data = search_res.json()
    s_items = s_data["items"] if isinstance(s_data, dict) and "items" in s_data else s_data
    assert len(s_items) >= 1

    # 13. Audit Logs REST
    audit_res = client.get(f"/api/v1/prompts/audit-logs?prompt_id={prompt_id}", headers=headers)
    assert audit_res.status_code == 200
    a_data = audit_res.json()
    a_items = a_data["items"] if isinstance(a_data, dict) and "items" in a_data else a_data
    assert len(a_items) >= 1

    # 14. Soft Delete, Restore & Purge
    del_res = client.delete(f"/api/v1/prompts/{cloned_id}", headers=headers)
    assert del_res.status_code == 200

    rest_res = client.post(f"/api/v1/prompts/{cloned_id}/restore", headers=headers)
    assert rest_res.status_code == 200

    purge_res = client.delete(f"/api/v1/prompts/{cloned_id}/purge", headers=headers)
    assert purge_res.status_code == 204
