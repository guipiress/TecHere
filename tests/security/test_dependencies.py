from unittest.mock import patch
from fastapi.security import HTTPAuthorizationCredentials
from backend.app.dependencies import get_current_user
import pytest

from fastapi import HTTPException
from jwt import InvalidTokenError


def test_get_current_user_success(mock_pool):
    fake_user = {
        "id": 10,
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "role": "CUSTOMER",
        "telephone": "11987654321",
        "cpf": "12345678901",
        "is_active": True,
    }

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="token-ficticio",
    )

    with patch(
        "backend.app.dependencies.decode_access_token",
        return_value={"sub": "10"},
    ):
        with patch(
            "backend.app.dependencies.fetch_user_by_id",
            return_value=fake_user,
        ) as mock_fetch_user:
            user = get_current_user(
                credentials=credentials,
                pool=mock_pool,
            )

    assert user == fake_user

    mock_fetch_user.assert_called_once_with(10, mock_pool)


def test_get_current_user_invalid_token(mock_pool):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="token-invalido",
    )

    with patch(
        "backend.app.dependencies.decode_access_token",
        side_effect=InvalidTokenError(),
    ):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(
                credentials=credentials,
                pool=mock_pool,
            )

    assert exc_info.value.status_code == 401


def test_get_current_user_user_not_found(mock_pool):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="token-ficticio",
    )

    with patch(
        "backend.app.dependencies.decode_access_token",
        return_value={"sub": "10"},
    ):
        with patch(
            "backend.app.dependencies.fetch_user_by_id",
            return_value=None,
        ):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(
                    credentials=credentials,
                    pool=mock_pool,
                )

    assert exc_info.value.status_code == 401


def test_get_current_user_inactive_user(mock_pool):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="token-ficticio",
    )

    fake_user = {
        "id": 10,
        "name": "Usuário Teste",
        "email": "teste@example.com",
        "is_active": False,
    }

    with patch(
        "backend.app.dependencies.decode_access_token",
        return_value={"sub": "10"},
    ):
        with patch(
            "backend.app.dependencies.fetch_user_by_id",
            return_value=fake_user,
        ):
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(
                    credentials=credentials,
                    pool=mock_pool,
                )

    assert exc_info.value.status_code == 401


def test_get_current_user_without_token(mock_pool):
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(
            credentials=None,
            pool=mock_pool,
        )

    assert exc_info.value.status_code == 401


def test_get_current_user_invalid_subject(mock_pool):
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="token-ficticio",
    )

    with patch(
        "backend.app.dependencies.decode_access_token",
        return_value={"sub": "abc"},
    ):
        with patch(
            "backend.app.dependencies.fetch_user_by_id"
        ) as mock_fetch_user:
            with pytest.raises(HTTPException) as exc_info:
                get_current_user(
                    credentials=credentials,
                    pool=mock_pool,
                )

    assert exc_info.value.status_code == 401
    mock_fetch_user.assert_not_called()
