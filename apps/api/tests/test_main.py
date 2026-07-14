from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    """
    Test that the root health check endpoint returns 200 and success status.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "healthy",
        "service": "Enterprise AI Marketing Operating System (EAIMOS)"
    }

def test_api_health_check():
    """
    Test that the versioned api health check endpoint returns 200 and success status.
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {
        "success": True,
        "status": "healthy",
        "version": "v1"
    }


def test_liveness_check():
    """
    Test that root and versioned liveness checks return 200.
    """
    response = client.get("/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"

    response = client.get("/api/v1/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_check(db_session):
    """
    Test readiness check. Returns 200 or 503 depending on mock states.
    """
    # Simply call ready endpoint to verify structure
    response = client.get("/ready")
    assert response.status_code in (200, 503)
    data = response.json()
    assert "status" in data
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "minio" in data["checks"]
    assert "ai_gateway" in data["checks"]

    response = client.get("/api/v1/ready")
    assert response.status_code in (200, 503)

