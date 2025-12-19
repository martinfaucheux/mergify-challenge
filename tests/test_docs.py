from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test that the API is running."""
    response = client.get("/docs")
    assert response.status_code == 200
