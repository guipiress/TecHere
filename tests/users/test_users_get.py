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



def test_get_users_success(client, mock_pool):
    fake_users = [
        {
            "id": 1,
            "name": "Ana",
            "email": "ana@example.com",
            "role": "customer",
            "telephone": "11987654321",
            "cpf": None,
            "is_active": True,
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        },
        {
            "id": 2,
            "name": "Bruno",
            "email": "bruno@example.com",
            "role": "customer",
            "telephone": "11912345678",
            "cpf": None,
            "is_active": True,
            "created_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 2, tzinfo=timezone.utc),
        },
    ]

    with patch(
        "backend.app.api.routes.users.fetch_users",
        return_value=fake_users,
    ) as mock_fetch_users:
        response = client.get("/users")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2
    assert data[0]["id"] == 1
    assert data[0]["name"] == "Ana"
    assert data[1]["id"] == 2
    assert data[1]["name"] == "Bruno"

    for user in data:
        assert "password" not in user
        assert "password_hash" not in user

    mock_fetch_users.assert_called_once_with(
    mock_pool,
    20,
    0,
    )


    
def test_get_users_with_pagination(client, mock_pool):
    with patch(
        "backend.app.api.routes.users.fetch_users",
        return_value=[],
    ) as mock_fetch_users:
        response = client.get("/users?limit=2&offset=2")

    assert response.status_code == 200
    assert response.json() == []

    mock_fetch_users.assert_called_once_with(
        mock_pool,
        2,
        2,
    )


    
def test_get_users_invalid_pagination(client):
    invalid_params = [
        {"limit": 0},
        {"limit": 101},
        {"offset": -1},
    ]

    for params in invalid_params:
        response = client.get("/users", params=params)

        assert response.status_code == 422, (
            f"Parâmetros inválidos aceitos: {params}"
        )



def test_get_users_does_not_expose_password_hash(client, mock_pool):
    fake_users = [
        {
            "id": 1,
            "name": "Ana",
            "email": "ana@example.com",
            "role": "customer",
            "telephone": "11987654321",
            "cpf": None,
            "is_active": True,
            "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
            "password_hash": "hash-ficticio-nao-utilizavel",
        }
    ]

    with patch(
        "backend.app.api.routes.users.fetch_users",
        return_value=fake_users,
    ) as mock_fetch_users:
        response = client.get("/users")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert "password" not in data[0]
    assert "password_hash" not in data[0]

    mock_fetch_users.assert_called_once_with(
        mock_pool,
        20,
        0,
    )



def test_get_users_invalid_pagination_does_not_call_repository(
    client,
    mock_pool,
):
    with patch(
        "backend.app.api.routes.users.fetch_users",
    ) as mock_fetch_users:
        response = client.get("/users?limit=0")

    assert response.status_code == 422
    mock_fetch_users.assert_not_called()
