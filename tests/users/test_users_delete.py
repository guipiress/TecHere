
from datetime import datetime, timezone
from unittest.mock import patch


def test_delete_user_success(client):
    fake_user = {
        "id": 1,
        "name": "Usuário Excluído",
        "email": "excluido@example.com",
        "role": "customer",
        "telephone": "11987654321",
        "cpf": None,
        "is_active": True,
        "created_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "updated_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
    }

    with patch(
        "backend.app.api.routes.users.delete_user",
        return_value=fake_user,
    ) as mock_delete_user:
        response = client.delete("/users/1")

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Usuário excluído com sucesso."
    assert data["user"]["id"] == 1
    assert data["user"]["name"] == "Usuário Excluído"
    assert data["user"]["email"] == "excluido@example.com"
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

    mock_delete_user.assert_called_once()



def test_delete_user_not_found(client):
    with patch(
        "backend.app.api.routes.users.delete_user",
        return_value=None,
    ) as mock_delete_user:
        response = client.delete("/users/999999")

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Usuário não encontrado."
    }

    mock_delete_user.assert_called_once()


