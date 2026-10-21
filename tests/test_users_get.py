from backend.app.main import app
from backend.app.dependencies import get_pool
from datetime import datetime, timezone
from unittest.mock import patch
from fastapi.testclient import TestClient


def test_get_user_not_found():
    app.dependency_overrides[get_pool] = lambda: object()

    try:
        with patch(
            "backend.app.api.routes.users.fetch_user_by_id",
            return_value=None,
        ):
            with TestClient(app) as client:
                response = client.get("/users/999999")

        assert response.status_code == 404
        assert response.json() == {"detail": "User not found"}

    finally:
        app.dependency_overrides.clear()



def test_get_user_by_id_success():
    fake_user = {
        "id": 1,
        "name": "Teste",
        "email": "teste@example.com",
        "role": "customer",
        "telephone": None,
        "cpf": None,
        "is_active": True,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }

    app.dependency_overrides[get_pool] = lambda: object()

    try:
        with patch(
            "backend.app.api.routes.users.fetch_user_by_id",
            return_value=fake_user,
        ) as mock_fetch:
            with TestClient(app) as client:
                response = client.get("/users/1")

        assert response.status_code == 200

        response_data = response.json()

        assert response_data["id"] == 1
        assert response_data["name"] == "Teste"
        assert response_data["email"] == "teste@example.com"

        assert "password" not in response_data
        assert "password_hash" not in response_data

        mock_fetch.assert_called_once()

    finally:
        app.dependency_overrides.clear()