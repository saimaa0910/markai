import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app
from api.models.ai_registry import AIModelRegistry
from api.routes.ai import sync_providers_and_models

client = TestClient(app)


def test_sync_registers_dynamic_groq_models(db_session):
    """Groq provider sync should persist dynamically fetched models into the registry."""
    mocked_response = MagicMock(status_code=200)
    mocked_response.json.return_value = {
        "data": [
            {"id": "openai/gpt-oss-120b"},
            {"id": "llama-3.3-70b-versatile"},
        ]
    }

    with patch("api.routes.ai.os.getenv", return_value="fake-groq-key"), patch(
        "api.routes.ai.httpx.Client"
    ) as mock_client:
        mock_client.return_value.__enter__.return_value.get.return_value = mocked_response
        sync_providers_and_models(db_session)

    groq_models = (
        db_session.query(AIModelRegistry)
        .filter(AIModelRegistry.provider == "groq")
        .all()
    )
    model_names = {model.model_name for model in groq_models}
    assert "openai/gpt-oss-120b" in model_names
    assert "llama-3.3-70b-versatile" in model_names


def test_conversations_gateway_lifecycle():
    """
    Test end-to-end conversations integration with the AI gateway.
    Covers:
      - Register / login
      - Creating conversations
      - Listing & search filtering
      - Renaming / updating conversations
      - Archive and Favorite toggling
      - Send non-streaming messages (routes to AIGateway)
      - Send SSE streaming messages (routes to AIGateway stream)
      - Deleting threads
    """
    # 1. Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "chat_user@example.com",
            "password": "securepassword123",
            "full_name": "Chat Agent User",
            "org_name": "Chat Org",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "chat_user@example.com", "password": "securepassword123"},
    ).json()
    token = login_res["access_token"]

    # Get organization ID
    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # Seed models list
    client.post("/api/v1/ai/models/sync", headers=headers)

    # 2. Create Chat Conversation
    conv_res = client.post(
        "/api/v1/chat/conversations/",
        json={
            "title": "Initial Discussion Title",
            "temperature": 0.7,
            "system_prompt": "You are a helpful assistant.",
            "model_name": "openai/gpt-oss-120b",
            "provider_name": "groq",
        },
        headers=headers,
    )
    assert conv_res.status_code == 201
    conv = conv_res.json()
    conv_id = conv["id"]
    assert conv["title"] == "Initial Discussion Title"
    assert conv["temperature"] == 0.7
    assert conv["model_name"] == "openai/gpt-oss-120b"
    assert conv["is_archived"] is False
    assert conv["is_favorite"] is False

    # 3. Retrieve details
    get_res = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Initial Discussion Title"

    # 4. Search and filter list
    search_res = client.get("/api/v1/chat/conversations/?query=Initial", headers=headers)
    assert search_res.status_code == 200
    assert len(search_res.json()) == 1

    search_empty = client.get("/api/v1/chat/conversations/?query=NotFound", headers=headers)
    assert search_empty.status_code == 200
    assert len(search_empty.json()) == 0

    # 5. Archive toggle
    archive_res = client.post(f"/api/v1/chat/conversations/{conv_id}/archive", headers=headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["is_archived"] is True

    # 6. Favorite toggle
    fav_res = client.post(f"/api/v1/chat/conversations/{conv_id}/favorite", headers=headers)
    assert fav_res.status_code == 200
    assert fav_res.json()["is_favorite"] is True

    # 7. Rename
    patch_res = client.patch(
        f"/api/v1/chat/conversations/{conv_id}",
        json={"title": "Renamed Conversation Title"},
        headers=headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["title"] == "Renamed Conversation Title"

    # 8. Post non-streaming message
    msg_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={
            "content": "Hello, gateway!",
            "model_name": "openai/gpt-oss-120b",
        },
        headers=headers,
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["role"] == "assistant"
    assert "content" in msg_data
    assert msg_data["model_used"] in ["openai/gpt-oss-120b", "llama3-70b-8192", "llama3-8b-8192"]
    assert msg_data["provider_used"] is not None

    # 9. Get thread messages history list
    msgs_res = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers)
    assert msgs_res.status_code == 200
    msgs_list = msgs_res.json()
    # Should contain user msg + assistant response (2 messages minimum)
    assert len(msgs_list) >= 2

    # 10. Post streaming response
    stream_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/stream",
        json={
            "content": "Give me a short greeting stream.",
            "model_name": "openai/gpt-oss-120b",
        },
        headers=headers,
    )
    assert stream_res.status_code == 200
    # Streaming responses yield text/event-stream headers
    assert "text/event-stream" in stream_res.headers["content-type"]
    
    # Parse SSE text output
    sse_text = stream_res.text
    assert "data: " in sse_text

    # 11. Delete conversation
    del_res = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert del_res.status_code == 204

    # Fetch details after delete (should raise 404)
    del_get = client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert del_get.status_code == 404
