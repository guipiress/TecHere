from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_get_user_not_found():
    response = client.get("/users/999999")

    assert response.status_code == 404