from datetime import datetime, timezone
from unittest.mock import patch
from backend.app.exceptions import UserEmailAlreadyExistsError
from backend.app.exceptions import UserCPFAlreadyExistsError
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.dependencies import get_pool


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



def test_create_user_success(client, mock_pool):
    fake_user = {
        "id": 10,
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "role": "customer",
        "telephone": "11987654321",
        "cpf": "12345678901",
        "is_active": True,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }

    payload = {
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "telephone": "11987654321",
        "cpf": "12345678901",
    }

    with patch(
        "backend.app.api.routes.users.hash_password",
        return_value="hash-ficticio",
    ) as mock_hash:
        with patch(
            "backend.app.api.routes.users.post_user",
            return_value=fake_user,
        ) as mock_post_user:
            response = client.post("/users", json=payload)

    assert response.status_code == 201

    data = response.json()

    assert data["id"] == 10
    assert data["name"] == "Usuário Teste"
    assert data["email"] == "teste@example.com"
    assert data["telephone"] == "11987654321"
    assert data["cpf"] == "12345678901"

    assert "password" not in data
    assert "password_hash" not in data
    assert "hash-ficticio" not in response.text

    mock_hash.assert_called_once_with("SenhaForte123!")

    mock_post_user.assert_called_once_with(
        mock_pool,
        name="Usuário Teste",
        email="teste@example.com",
        password_hash="hash-ficticio",
        telephone="11987654321",
        cpf="12345678901",
    )



def test_create_user_duplicate_email(client):
    payload = {
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "telephone": "11987654321",
        "cpf": "12345678901",
    }

    with patch(
        "backend.app.api.routes.users.hash_password",
        return_value="hash-ficticio",
    ):
        with patch(
            "backend.app.api.routes.users.post_user",
            side_effect=UserEmailAlreadyExistsError(),
        ):
            response = client.post("/users", json=payload)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Este e-mail já está cadastrado."
    }



def test_create_user_duplicate_cpf(client):
    payload = {
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "telephone": "11987654321",
        "cpf": "12345678901",
    }

    with patch(
        "backend.app.api.routes.users.hash_password",
        return_value="hash-ficticio",
    ):
        with patch(
            "backend.app.api.routes.users.post_user",
            side_effect=UserCPFAlreadyExistsError(),
        ):
            response = client.post("/users", json=payload)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Este CPF já está cadastrado."
    }



def test_create_user_invalid_email(client):
    payload = {
        "name": "Usuário Teste",
        "email": "email-invalido",
        "password": "SenhaForte123!",
        "telephone": "11987654321",
        "cpf": "12345678901",
    }

    with patch(
        "backend.app.api.routes.users.post_user"
    ) as mock_post_user:
        response = client.post("/users", json=payload)

    assert response.status_code == 422
    mock_post_user.assert_not_called()



def test_create_user_short_password(client):
    payload = {
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password": "1234567",
        "telephone": "11987654321",
        "cpf": "12345678901",
    }

    with patch(
        "backend.app.api.routes.users.post_user"
    ) as mock_post_user:
        response = client.post("/users", json=payload)

    assert response.status_code == 422
    mock_post_user.assert_not_called()



def test_create_user_invalid_cpf(client):
    payload = {
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "telephone": "11987654321",
        "cpf": "1234567890",
    }

    with patch(
        "backend.app.api.routes.users.post_user"
    ) as mock_post_user:
        response = client.post("/users", json=payload)

    assert response.status_code == 422
    mock_post_user.assert_not_called()
