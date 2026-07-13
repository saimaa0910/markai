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
