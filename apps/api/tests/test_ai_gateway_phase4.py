import pytest
import uuid
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_rag_and_knowledge_base():
    """
    Verify uploading a document, chunking, embeddings similarity lookup,
    and RAG context injection into chat completions.
    """
    # 1. Register and login User
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "rag_tester@example.com",
            "password": "strongpassword",
            "full_name": "RAG Tester",
            "org_name": "RAG Organization",
        },
    )
    login = client.post(
        "/api/v1/auth/login",
        data={"username": "rag_tester@example.com", "password": "strongpassword"},
    ).json()
    token = login["access_token"]

    # Retrieve Org details
    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    headers = {"Authorization": f"Bearer {token}", "X-Organization-ID": org_id}

    # 2. Upload Knowledge Document
    content_text = (
        "Viptant is an Enterprise AI Marketing Operating System. "
        "It was founded in the year 2026. "
        "The core technologies utilized on the backend include Python, FastAPI, SQLAlchemy, and PostgreSQL. "
        "The frontend is built using Next.js, React 19, and Tailwind CSS. "
        "Viptant enables automated multi-channel campaign generation, CRM integration, and auditing."
    )
    upload_res = client.post(
        "/api/v1/ai/knowledge/",
        json={
            "title": "Viptant Overview",
            "file_type": "md",
            "content": content_text,
        },
        headers=headers,
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["title"] == "Viptant Overview"
    assert len(doc_data["chunks"]) > 0

    # 3. Query Knowledge Similarity
    query_res = client.post(
        "/api/v1/ai/knowledge/query",
        json={
            "query_text": "What core backend technologies does Viptant use?",
            "limit": 2,
        },
        headers=headers,
    )
    assert query_res.status_code == 200
    chunks = query_res.json()
    assert len(chunks) > 0
    assert "backend" in chunks[0]["content"]

    # 4. Create Conversation Session
    conv_res = client.post(
        "/api/v1/ai/conversations/",
        json={"title": "RAG Session"},
        headers=headers,
    )
    assert conv_res.status_code == 201
    conv = conv_res.json()

    # 5. Send message with RAG context injection
    msg_res = client.post(
        f"/api/v1/ai/conversations/{conv['id']}/messages",
        json={
            "content": "List backend technologies of Viptant",
            "model_name": "gpt-4o-mini",
            "rag_enabled": True,
        },
        headers=headers,
    )
    assert msg_res.status_code == 201
    msg_data = msg_res.json()
    assert msg_data["role"] == "assistant"
    
    # Assert that RAG context was successfully fetched and injected into the prompt context prefix
    content_received = msg_data["content"]
    assert "System Context:" in content_received
    assert "Use the following knowledge base context" in content_received
    assert "backend technologies" in content_received or "FastAPI" in content_received
