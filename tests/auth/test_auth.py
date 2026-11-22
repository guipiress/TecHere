from unittest.mock import patch
from backend.app.security import decode_access_token


def test_login_success(client, mock_pool):
    fake_user = {
        "id": 10,
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password_hash": "hash-ficticio",
        "role": "CUSTOMER",
        "is_active": True,
    }

    payload = {
        "email": "teste@example.com",
        "password": "SenhaForte123!",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth",
        return_value=fake_user,
    ) as mock_fetch_user:
        with patch(
            "backend.app.api.routes.auth.verify_password",
            return_value=True,
        ) as mock_verify:
            response = client.post("/auth/login", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"

    token_data = decode_access_token(data["access_token"])

    assert token_data["sub"] == "10"

    mock_fetch_user.assert_called_once_with(
        mock_pool,
        "teste@example.com",
    )

    mock_verify.assert_called_once_with(
        "SenhaForte123!",
        "hash-ficticio",
    )


def test_login_invalid_password(client):
    fake_user = {
        "id": 10,
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password_hash": "hash-ficticio",
        "role": "CUSTOMER",
        "is_active": True,
    }

    payload = {
        "email": "teste@example.com",
        "password": "SenhaErrada123!",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth",
        return_value=fake_user,
    ):
        with patch(
            "backend.app.api.routes.auth.verify_password",
            return_value=False,
        ):
            response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "E-mail ou senha inválidos."
    }


def test_login_user_not_found(client):
    payload = {
        "email": "inexistente@example.com",
        "password": "SenhaForte123!",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth",
        return_value=None,
    ) as mock_fetch_user:
        with patch(
            "backend.app.api.routes.auth.verify_password"
        ) as mock_verify:
            response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "E-mail ou senha inválidos."
    }

    mock_verify.assert_not_called()
    mock_fetch_user.assert_called_once()


def test_login_inactive_user(client):
    fake_user = {
        "id": 10,
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "password_hash": "hash-ficticio",
        "role": "CUSTOMER",
        "is_active": False,
    }

    payload = {
        "email": "teste@example.com",
        "password": "SenhaForte123!",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth",
        return_value=fake_user,
    ):
        with patch(
            "backend.app.api.routes.auth.verify_password",
            return_value=True,
        ):
            response = client.post("/auth/login", json=payload)

    assert response.status_code == 401
    assert response.json() == {
        "detail": "E-mail ou senha inválidos."
    }



def test_login_invalid_email(client):
    payload = {
        "email": "email-invalido",
        "password": "SenhaForte123!",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth"
    ) as mock_fetch_user:
        response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    mock_fetch_user.assert_not_called()



def test_login_empty_password(client):
    payload = {
        "email": "teste@example.com",
        "password": "",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth"
    ) as mock_fetch_user:
        response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    mock_fetch_user.assert_not_called()



def test_login_unknown_field(client):
    payload = {
        "email": "teste@example.com",
        "password": "SenhaForte123!",
        "role": "ADMIN",
    }

    with patch(
        "backend.app.api.routes.auth.fetch_user_by_email_for_auth"
    ) as mock_fetch_user:
        response = client.post("/auth/login", json=payload)

    assert response.status_code == 422
    mock_fetch_user.assert_not_called()
