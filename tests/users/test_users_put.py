from backend.app.exceptions import UserEmailAlreadyExistsError
from backend.app.exceptions import UserCPFAlreadyExistsError
from datetime import datetime, timezone
from unittest.mock import patch


def test_update_user_success(client, mock_pool):
    fake_user = {
        "id": 1,
        "name": "Nome Atualizado",
        "email": "teste@example.com",
        "role": "customer",
        "telephone": "11987654321",
        "cpf": None,
        "is_active": True,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }

    payload = {
        "name": "Nome Atualizado",
        "telephone": "11987654321",
    }

    with patch(
        "backend.app.api.routes.users.put_user",
        return_value=fake_user,
    ) as mock_put_user:
        response = client.put("/users/1", json=payload)

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "Nome Atualizado"
    assert data["telephone"] == "11987654321"
    assert "password" not in data
    assert "password_hash" not in data

    mock_put_user.assert_called_once()



def test_update_user_not_found(client):
    payload = {
        "name": "Nome Atualizado",
        "telephone": "11987654321",
    }

    with patch(
        "backend.app.api.routes.users.put_user",
        return_value=None,
    ) as mock_put_user:
        response = client.put("/users/999999", json=payload)

    assert response.status_code == 404
    assert response.json() == {
    "detail": "Usuário não encontrado."
    }

    mock_put_user.assert_called_once()



def test_update_user_invalid_email(client):
    payload = {
        "email": "email-invalido",
    }

    with patch(
        "backend.app.api.routes.users.put_user"
    ) as mock_put_user:
        response = client.put("/users/1", json=payload)

    assert response.status_code == 422
    mock_put_user.assert_not_called()



def test_update_user_duplicate_email(client):
    payload = {
        "email": "existente@example.com",
    }

    with patch(
        "backend.app.api.routes.users.put_user",
        side_effect=UserEmailAlreadyExistsError(),
    ) as mock_put_user:
        response = client.put("/users/1", json=payload)

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Este e-mail já está cadastrado."
    }

    mock_put_user.assert_called_once()



def test_update_user_empty_name(client):
    payload = {
        "name": "",
    }

    with patch(
        "backend.app.api.routes.users.put_user"
    ) as mock_put_user:
        response = client.put("/users/1", json=payload)

    assert response.status_code == 422
    mock_put_user.assert_not_called()
