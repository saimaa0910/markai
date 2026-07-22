import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_prompt_platform_e2e():
    """
    E2E test verifying all Phase 4 Enterprise Prompt Platform endpoints,
    database integration, and execution workflows.
    """
    # 1. Register and Login to retrieve org_id and authorization token
    register_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "prompter@example.com",
            "password": "strongpassword123",
            "full_name": "Prompt Architect",
            "org_name": "Prompt Lab Inc",
        },
    )
    assert register_res.status_code == 201
    
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "prompter@example.com", "password": "strongpassword123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Fetch org ID
    orgs_res = client.get("/api/v1/organizations/", headers=headers)
    assert orgs_res.status_code == 200
    org_id = orgs_res.json()[0]["id"]
    headers["X-Organization-ID"] = org_id

    # 2. Test Collections & Folders API
    col_res = client.post(
        "/api/v1/ai/prompts/collections",
        json={"name": "Sales Campaigns", "description": "Collections for sales cold outreach prompts"},
        headers=headers,
    )
    assert col_res.status_code == 200
    col_id = col_res.json()["id"]

    list_col_res = client.get("/api/v1/ai/prompts/collections", headers=headers)
    assert list_col_res.status_code == 200
    assert len(list_col_res.json()) >= 1

    folder_res = client.post(
        "/api/v1/ai/prompts/folders",
        json={"name": "Q3 Outreach", "collection_id": col_id},
        headers=headers,
    )
    assert folder_res.status_code == 200
    folder_id = folder_res.json()["id"]

    list_folders_res = client.get(
        f"/api/v1/ai/prompts/folders?collection_id={col_id}", headers=headers
    )
    assert list_folders_res.status_code == 200
    assert len(list_folders_res.json()) >= 1

    # 3. Test Prompt Create & Version Increments
    prompt_create_res = client.post(
        "/api/v1/ai/prompts/",
        json={
            "name": "Cold Outreach",
            "content": "Write a sales cold email template to {{contact_name}} about our {{product_name}} service. Current date is {{current_date}}.",
            "category": "Sales",
            "tags": "sales,cold-email",
            "is_shared": True
        },
        headers=headers,
    )
    assert prompt_create_res.status_code == 201
    prompt_data = prompt_create_res.json()
    assert prompt_data["version"] == 1
    
    # Update prompt to v2
    prompt_update_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach",
        json={
            "content": "Write a premium cold email template to {{contact_name}} about {{product_name}} with special discount. Date: {{current_date}}.",
            "category": "Sales",
            "tags": "sales,discount",
            "is_shared": True
        },
        headers=headers,
    )
    print("RESPONSE JSON:", prompt_update_res.status_code, prompt_update_res.json())
    assert prompt_update_res.status_code == 200
    assert prompt_update_res.json()["version"] == 2

    # Fetch History
    history_res = client.get("/api/v1/ai/prompts/Cold Outreach/history", headers=headers)
    assert history_res.status_code == 200
    assert len(history_res.json()) == 2

    # 4. Compare Versions (Unified Diff)
    diff_res = client.get(
        "/api/v1/ai/prompts/Cold Outreach/diff?version_a=1&version_b=2",
        headers=headers,
    )
    assert diff_res.status_code == 200
    assert "diff" in diff_res.json()

    # 5. Duplicate Prompt Family
    dup_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/duplicate?new_name=Cold Outreach Copy",
        headers=headers,
    )
    assert dup_res.status_code == 200
    assert dup_res.json()["name"] == "Cold Outreach Copy"
    assert dup_res.json()["version"] == 1

    # 6. Rollback Prompt Version
    rollback_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/rollback?version=1",
        headers=headers,
    )
    assert rollback_res.status_code == 200
    # Rollback inserts v3 containing the content of v1
    assert rollback_res.json()["version"] == 3
    assert "service. Current date is {{current_date}}" in rollback_res.json()["content"]

    # 7. Execute Prompt (Template + Variables rendering + system prompt + AIGateway call)
    exec_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/execute",
        json={
            "variables": {
                "contact_name": "John Doe",
                "product_name": "Viptant Enterprise Prompting"
            },
            "model_name": "gemini-1.5-flash",
            "system_prompt": "You are a top sales closer agent.",
            "temperature": 0.5
        },
        headers=headers,
    )
    assert exec_res.status_code == 200
    exec_data = exec_res.json()
    assert "output" in exec_data
    assert exec_data["provider"] in ["google", "groq", "openai", "anthropic", "openrouter", "system"]
    assert "tokens_used" in exec_data
    assert "cost_usd" in exec_data

    # 8. Optimize Prompt Suggestions Audit
    opt_res = client.post(
        "/api/v1/ai/prompts/optimize",
        json={
            "content": "Summarize this data: {{my_data}}"
        },
        headers=headers,
    )
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert "token_efficiency" in opt_data
    assert "instruction_clarity" in opt_data
    assert len(opt_data["suggestions"]) >= 1

    # 9. Test Case & Evaluation Lab
    tc_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/testcases",
        json={
            "name": "Outreach Test 1",
            "inputs": {
                "contact_name": "Alice Smith",
                "product_name": "Super AI CRM"
            },
            "expected_output": "Cold sales email outreach template"
        },
        headers=headers,
    )
    assert tc_res.status_code == 200
    tc_id = tc_res.json()["id"]

    list_tcs_res = client.get("/api/v1/ai/prompts/Cold Outreach/testcases", headers=headers)
    assert list_tcs_res.status_code == 200
    assert len(list_tcs_res.json()) >= 1

    # Run evaluations
    eval_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/evaluate?model_name=gemini-1.5-flash",
        headers=headers,
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.json()
    assert len(eval_data) >= 1
    assert "correctness_score" in eval_data[0]
    assert "grounding_score" in eval_data[0]
    assert "overall_score" in eval_data[0]
    assert eval_data[0]["status"] in ["pass", "warning", "fail"]

    # 10. Dashboard Stats
    stats_res = client.get("/api/v1/ai/prompts/dashboard/stats", headers=headers)
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["totalPrompts"] >= 1
    assert stats_data["totalExecutions"] >= 1
    assert len(stats_data["categoriesBreakdown"]) >= 1

    # 11. Export & Import Packs
    export_res = client.get("/api/v1/ai/prompts/export?format_type=csv", headers=headers)
    assert export_res.status_code == 200
    exported_csv = export_res.json()["file_content"]
    assert "Cold Outreach" in exported_csv

    import_res = client.post(
        "/api/v1/ai/prompts/import",
        json={
            "file_content": "name,content,category,tags\nImported CRM cold call,Write script Cold outreach script,CRM,phone",
            "format_type": "csv"
        },
        headers=headers,
    )
    assert import_res.status_code == 200
    assert len(import_res.json()) == 1
    assert import_res.json()[0]["name"] == "Imported CRM cold call"

    # 12. Share Prompt Link & Public Retrieval
    share_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/share",
        json={"visibility": "public", "expires_in_days": 7, "is_editable": False},
        headers=headers,
    )
    assert share_res.status_code == 200
    share_token = share_res.json()["share_token"]

    public_get_res = client.get(f"/api/v1/ai/prompts/shared/{share_token}")
    assert public_get_res.status_code == 200
    assert public_get_res.json()["name"] == "Cold Outreach"

    # 13. Search API
    search_res = client.post(
        "/api/v1/ai/prompts/search",
        json={"query": "Outreach", "is_archived": False},
        headers=headers,
    )
    assert search_res.status_code == 200
    assert len(search_res.json()) >= 1

    # 14. Recent Prompts
    recent_res = client.get("/api/v1/ai/prompts/recent?limit=5", headers=headers)
    assert recent_res.status_code == 200
    assert len(recent_res.json()) >= 1

    # 15. Bulk Actions
    bulk_res = client.post(
        "/api/v1/ai/prompts/bulk-action",
        json={"action": "tag", "prompt_names": ["Cold Outreach"], "payload": {"tag": "bulk-tested"}},
        headers=headers,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["affected_count"] == 1

    # 16. Streaming Prompt Execution (SSE)
    stream_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/stream",
        json={
            "variables": {"contact_name": "Dave", "product_name": "Viptant AI"},
            "model_name": "gemini-1.5-flash",
        },
        headers=headers,
    )
    assert stream_res.status_code == 200
    assert "data:" in stream_res.text

    # 17. Dynamic Provider Models API (Groq)
    groq_models_res = client.get("/api/v1/ai/providers/groq/models", headers=headers)
    assert groq_models_res.status_code == 200
    assert len(groq_models_res.json()) >= 1
    model_names = [m["model_name"] for m in groq_models_res.json()]
    assert "llama3-70b-8192" in model_names

    # 18. Dual Versioning: Draft & Release
    draft_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/draft",
        json={
            "name": "Cold Outreach",
            "content": "Draft email to {{contact_name}} for {{product_name}}.",
            "category": "Sales",
        },
        headers=headers,
    )
    assert draft_res.status_code == 200
    assert draft_res.json()["status"] == "draft"

    release_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/release?release_notes=Published+v4+stable",
        headers=headers,
    )
    assert release_res.status_code == 200
    assert release_res.json()["status"] == "approved"

    # 19. Rollback Version
    rollback_res = client.post(
        "/api/v1/ai/prompts/Cold Outreach/rollback?target_version=1",
        headers=headers,
    )
    assert rollback_res.status_code == 200
    assert rollback_res.json()["status"] == "draft"

    # 20. Permanent Purge Prompt Cascade
    purge_res = client.delete("/api/v1/ai/prompts/Imported CRM cold call/purge", headers=headers)
    assert purge_res.status_code == 204
