import json
import uuid
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_conversations_extended_features():
    """
    Test extended chat conversations features.
    Covers:
      - Pinning threads
      - Soft-delete restores
      - Message deletion
      - Bookmarks CRUD
      - Sharing tokens
      - Collaboration participants
      - Exporting messages
      - Telemetry analytics
    """
    # 1. Register and login
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "extended_user@example.com",
            "password": "securepassword123",
            "full_name": "Extended Test User",
            "org_name": "Extended Org",
        },
    )
    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": "extended_user@example.com", "password": "securepassword123"},
    ).json()
    token = login_res["access_token"]

    # Get organization ID
    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 2. Create Chat Conversation
    conv_res = client.post(
        "/api/v1/chat/conversations/",
        json={
            "title": "Extended Features Chat",
            "temperature": 0.7,
            "model_name": "openai/gpt-oss-120b",
            "provider_name": "groq",
        },
        headers=headers,
    )
    assert conv_res.status_code == 201
    conv = conv_res.json()
    conv_id = conv["id"]

    # 3. Pin conversation
    pin_res = client.post(f"/api/v1/chat/conversations/{conv_id}/pin", headers=headers)
    assert pin_res.status_code == 200
    assert pin_res.json()["is_pinned"] is True

    unpin_res = client.post(f"/api/v1/chat/conversations/{conv_id}/pin", headers=headers)
    assert unpin_res.status_code == 200
    assert unpin_res.json()["is_pinned"] is False

    # 4. Bookmarks CRUD
    bookmark_res = client.post(f"/api/v1/chat/conversations/{conv_id}/bookmarks", headers=headers)
    assert bookmark_res.status_code == 201
    assert bookmark_res.json()["conversation_id"] == conv_id

    bookmarks_list = client.get("/api/v1/chat/conversations/bookmarks", headers=headers)
    assert bookmarks_list.status_code == 200
    assert len(bookmarks_list.json()) == 1

    del_bookmark = client.delete(f"/api/v1/chat/conversations/{conv_id}/bookmarks", headers=headers)
    assert del_bookmark.status_code == 204

    # 5. Shares CRUD
    share_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/share",
        json={"permission": "viewer"},
        headers=headers,
    )
    assert share_res.status_code == 200
    share_data = share_res.json()
    token_str = share_data["share_token"]
    assert token_str.startswith("share_")

    public_get = client.get(f"/api/v1/chat/conversations/share/{token_str}")
    assert public_get.status_code == 200

    # 6. Messages CRUD & deletion
    msg_res = client.post(
        f"/api/v1/chat/conversations/{conv_id}/messages",
        json={
            "content": "Verify message deletion",
            "model_name": "openai/gpt-oss-120b",
        },
        headers=headers,
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    
    # Message list should contain user and assistant messages
    msgs_before = client.get(f"/api/v1/chat/conversations/{conv_id}/messages", headers=headers).json()
    msg_id = msgs_before[0]["id"]
    
    del_msg_res = client.delete(f"/api/v1/chat/conversations/{conv_id}/messages/{msg_id}", headers=headers)
    assert del_msg_res.status_code == 204

    # 7. Exports
    export_md = client.get(f"/api/v1/chat/conversations/{conv_id}/export?format=markdown", headers=headers)
    assert export_md.status_code == 200
    assert "text/markdown" in export_md.headers["content-type"]

    export_json = client.get(f"/api/v1/chat/conversations/{conv_id}/export?format=json", headers=headers)
    assert export_json.status_code == 200
    assert "application/json" in export_json.headers["content-type"]

    # 8. Collaboration Participants
    participants_res = client.get(f"/api/v1/chat/conversations/{conv_id}/participants", headers=headers)
    assert participants_res.status_code == 200
    # Should list owner
    assert len(participants_res.json()) == 1
    assert participants_res.json()[0]["role"] == "owner"

    # 9. Telemetry Analytics
    analytics_res = client.get("/api/v1/chat/conversations/analytics", headers=headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert "total_conversations" in analytics_data
    assert "total_messages" in analytics_data
    assert "daily_stats" in analytics_data

    # 10. Soft-delete and Restore
    del_conv = client.delete(f"/api/v1/chat/conversations/{conv_id}", headers=headers)
    assert del_conv.status_code == 204

    # Should raise 404
    assert client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers).status_code == 404

    restore_conv = client.post(f"/api/v1/chat/conversations/{conv_id}/restore", headers=headers)
    assert restore_conv.status_code == 200

    # Should load correctly after restore
    assert client.get(f"/api/v1/chat/conversations/{conv_id}", headers=headers).status_code == 200
