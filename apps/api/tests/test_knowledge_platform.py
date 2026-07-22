import os
import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_knowledge_platform_lifecycle():
    """
    Verify the complete RAG Knowledge Platform REST API endpoints and service pipelines.
    """
    # 1. Register and login User A (creates Org A)
    rand_id = str(uuid.uuid4())[:8]
    register_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_knowledge_{rand_id}@example.com",
            "password": "superpassword123",
            "full_name": "User Knowledge",
            "org_name": f"Org Knowledge {rand_id}",
        },
    )
    assert register_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": f"user_knowledge_{rand_id}@example.com", "password": "superpassword123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    # Retrieve Org ID
    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id
    }

    # 2. Test Collections CRUD
    col_res = client.post(
        "/api/v1/ai/knowledge/collections",
        json={
            "name": "Finance & Analytics",
            "description": "Financial reports and analytical matrices.",
            "visibility": "ORGANIZATION"
        },
        headers=headers,
    )
    assert col_res.status_code == 201
    col_data = col_res.json()
    assert col_data["name"] == "Finance & Analytics"
    assert col_data["organization_id"] == org_id
    collection_id = col_data["id"]

    list_cols_res = client.get(
        "/api/v1/ai/knowledge/collections",
        headers=headers,
    )
    assert list_cols_res.status_code == 200
    assert len(list_cols_res.json()) >= 1

    # 3. Test Folder creation inside Collection
    folder_res = client.post(
        "/api/v1/ai/knowledge/folders",
        json={
            "name": "Q3 Reports",
            "collection_id": collection_id
        },
        headers=headers,
    )
    assert folder_res.status_code == 201
    folder_data = folder_res.json()
    assert folder_data["name"] == "Q3 Reports"
    assert folder_data["collection_id"] == collection_id
    folder_id = folder_data["id"]

    # 4. Upload raw text document via Legacy API
    upload_res = client.post(
        "/api/v1/ai/knowledge/",
        json={
            "title": "API Route Limits Guideline",
            "file_type": "TXT",
            "content": "All API routes must apply rate limits. Specifically, AI playground routes are restricted to 10 requests per minute to prevent provider billing spikes. High throughput integrations should request exemption headers."
        },
        headers=headers,
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    assert doc_data["title"] == "API Route Limits Guideline"
    assert doc_data["status"] in ["completed", "pending"]
    if doc_data.get("metadata_info"):
        assert "checksum" in doc_data["metadata_info"]
    doc_id = doc_data["id"]

    # Autocomplete suggestions test
    autocomplete_res = client.get(
        "/api/v1/ai/knowledge/search/autocomplete?q=API",
        headers=headers,
    )
    assert autocomplete_res.status_code == 200
    assert "API Route Limits Guideline" in autocomplete_res.json()

    # Rebuild single document embeddings test
    rebuild_res = client.post(
        f"/api/v1/ai/knowledge/documents/{doc_id}/rebuild",
        headers=headers,
    )
    assert rebuild_res.status_code == 200
    assert rebuild_res.json()["status"] == "pending"

    # Rebuild collection embeddings test
    rebuild_col_res = client.post(
        f"/api/v1/ai/knowledge/collections/{collection_id}/rebuild",
        headers=headers,
    )
    assert rebuild_col_res.status_code == 200
    assert "triggered" in rebuild_col_res.json()["message"]

    # 5. Query vector search for similar chunks (Legacy API)
    query_res = client.post(
        "/api/v1/ai/knowledge/query",
        json={
            "query_text": "What is the rate limit for AI playground?",
            "limit": 3
        },
        headers=headers,
    )
    assert query_res.status_code == 200
    query_data = query_res.json()
    assert len(query_data) >= 1
    assert "rate limit" in query_data[0]["content"].lower()

    # 6. Execute RAG query with citations
    rag_res = client.post(
        "/api/v1/ai/knowledge/rag",
        json={
            "query_text": "How many requests per minute are allowed for AI playground?",
            "limit": 3,
            "search_type": "SEMANTIC"
        },
        headers=headers,
    )
    assert rag_res.status_code == 200
    rag_data = rag_res.json()
    assert "answer" in rag_data
    assert len(rag_data["citations"]) >= 1
    assert rag_data["citations"][0]["document_id"] == doc_id
    assert "confidence_score" in rag_data

    # 7. Check Ingestion jobs processing queue
    queue_res = client.get(
        "/api/v1/ai/knowledge/queue",
        headers=headers,
    )
    assert queue_res.status_code == 200
    queue_data = queue_res.json()
    assert len(queue_data) >= 1

    # 8. Check Dashboard stats API
    stats_res = client.get(
        "/api/v1/ai/knowledge/dashboard/stats",
        headers=headers,
    )
    assert stats_res.status_code == 200
    stats_data = stats_res.json()
    assert stats_data["stats"]["document_count"] >= 1
    assert stats_data["stats"]["collection_count"] >= 1

    # 9. Clean up resources
    del_doc_res = client.delete(
        f"/api/v1/ai/knowledge/documents/{doc_id}",
        headers=headers,
    )
    assert del_doc_res.status_code == 204

    del_col_res = client.delete(
        f"/api/v1/ai/knowledge/collections/{collection_id}",
        headers=headers,
    )
    assert del_col_res.status_code == 204
