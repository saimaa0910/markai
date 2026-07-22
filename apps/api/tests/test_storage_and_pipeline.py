import uuid
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.services.storage_service import MinIOService

client = TestClient(app)


def test_minio_storage_service_unit():
    """Verify MinIOService upload, presigned url generation, download, and deletion."""
    test_data = b"Enterprise EAIMOS MinIO Unit Test Content"
    object_name = f"test_unit_{uuid.uuid4()}.txt"

    # 1. Upload
    uploaded_key = MinIOService.upload_file(
        file_bytes=test_data,
        object_name=object_name,
        content_type="text/plain"
    )
    assert uploaded_key == object_name

    # 2. Presigned URL
    url = MinIOService.get_presigned_url(object_name)
    assert url is not None
    assert len(url) > 0

    # 3. Download
    downloaded_bytes = MinIOService.download_file_bytes(object_name)
    assert downloaded_bytes == test_data

    # 4. Checksum
    sha256 = MinIOService.compute_sha256(test_data)
    assert len(sha256) == 64

    # 5. Delete
    deleted = MinIOService.delete_file(object_name)
    assert deleted is True


def test_document_management_extended_routes():
    """Verify extended Document Management REST APIs (replace, move, restore, tags, preview, purge)."""
    # 1. Login user
    rand_id = str(uuid.uuid4())[:8]
    register_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": f"user_docmgmt_{rand_id}@example.com",
            "password": "superpassword123",
            "full_name": "User DocMgmt",
            "org_name": f"Org DocMgmt {rand_id}",
        },
    )
    assert register_res.status_code == 201

    login_res = client.post(
        "/api/v1/auth/login",
        data={"username": f"user_docmgmt_{rand_id}@example.com", "password": "superpassword123"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]

    orgs = client.get(
        "/api/v1/organizations/",
        headers={"Authorization": f"Bearer {token}"},
    ).json()
    org_id = orgs[0]["id"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Organization-ID": org_id
    }

    # 2. Upload file via /upload endpoint
    files = {"file": ("test_doc.txt", b"First initial version content for test document.", "text/plain")}
    upload_res = client.post(
        "/api/v1/ai/knowledge/upload",
        files=files,
        headers=headers,
    )
    assert upload_res.status_code == 202
    doc_data = upload_res.json()
    doc_id = doc_data["id"]

    # 3. Preview document content
    preview_res = client.get(
        f"/api/v1/ai/knowledge/documents/{doc_id}/preview",
        headers=headers,
    )
    assert preview_res.status_code == 200
    assert len(preview_res.content) > 0

    # 4. Update tags
    tags_res = client.patch(
        f"/api/v1/ai/knowledge/documents/{doc_id}/tags",
        json=["finance", "q3", "confidential"],
        headers=headers,
    )
    assert tags_res.status_code == 200
    assert tags_res.json()["metadata_info"]["tags"] == ["finance", "q3", "confidential"]

    # 5. Move document
    new_col_res = client.post(
        "/api/v1/ai/knowledge/collections",
        json={"name": "Archive Collection", "visibility": "ORGANIZATION"},
        headers=headers,
    )
    assert new_col_res.status_code == 201
    new_col_id = new_col_res.json()["id"]

    move_res = client.post(
        f"/api/v1/ai/knowledge/documents/{doc_id}/move",
        json={"collection_id": new_col_id},
        headers=headers,
    )
    assert move_res.status_code == 200
    assert move_res.json()["collection_id"] == new_col_id

    # 6. Replace file version
    replace_files = {"file": ("test_doc_v2.txt", b"Second updated version content for test document.", "text/plain")}
    replace_res = client.post(
        f"/api/v1/ai/knowledge/documents/{doc_id}/replace",
        files=replace_files,
        headers=headers,
    )
    assert replace_res.status_code == 200
    assert replace_res.json()["title"] == "test_doc_v2.txt"

    # 7. Soft delete and Restore
    del_res = client.delete(
        f"/api/v1/ai/knowledge/documents/{doc_id}",
        headers=headers,
    )
    assert del_res.status_code == 204

    restore_res = client.post(
        f"/api/v1/ai/knowledge/documents/{doc_id}/restore",
        headers=headers,
    )
    assert restore_res.status_code == 200

    # 8. Permanent purge
    purge_res = client.delete(
        f"/api/v1/ai/knowledge/documents/{doc_id}/purge",
        headers=headers,
    )
    assert purge_res.status_code == 204
