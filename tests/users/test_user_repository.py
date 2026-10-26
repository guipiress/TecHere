from unittest.mock import MagicMock, PropertyMock, patch
from backend.repository.user import fetch_users, fetch_user_by_id, post_user, put_user, delete_user
import pytest
from psycopg import errors
from backend.app.exceptions import (
    UserEmailAlreadyExistsError,
    UserCPFAlreadyExistsError,
)


def test_fetch_users_executes_query_with_pagination():
    pool = MagicMock()

    fake_users = [
        {"id": 3, "name": "Ana"},
        {"id": 4, "name": "Bruno"},
    ]

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = fake_users

    result = fetch_users(pool, limit=2, offset=2)

    assert result == fake_users

    cursor.execute.assert_called_once()

    query, params = cursor.execute.call_args.args

    assert "FROM public.users" in query
    assert "ORDER BY id" in query
    assert "LIMIT %s OFFSET %s" in query
    assert params == (2, 2)

    cursor.fetchall.assert_called_once_with()



def test_fetch_users_returns_empty_list():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchall.return_value = []

    result = fetch_users(pool, limit=20, offset=100)

    assert result == []
    cursor.fetchall.assert_called_once_with()



def test_fetch_users_closes_cursor_and_connection_contexts():
    pool = MagicMock()

    connection_context = pool.connection.return_value
    cursor_context = connection_context.__enter__.return_value
    cursor_manager = cursor_context.cursor.return_value
    cursor = cursor_manager.__enter__.return_value

    cursor.fetchall.return_value = []

    result = fetch_users(pool, limit=20, offset=0)

    assert result == []

    connection_context.__enter__.assert_called_once()
    connection_context.__exit__.assert_called_once()

    cursor_manager.__enter__.assert_called_once()
    cursor_manager.__exit__.assert_called_once()



def test_fetch_users_propagates_database_error():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    cursor.execute.side_effect = RuntimeError("Database query failed")

    with pytest.raises(RuntimeError, match="Database query failed"):
        fetch_users(pool, limit=20, offset=0)



def test_fetch_user_by_id_returns_user():
    pool = MagicMock()

    fake_user = {
        "id": 7,
        "name": "Ana",
        "email": "ana@example.com",
    }

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = fake_user

    result = fetch_user_by_id(7, pool)

    assert result == fake_user

    cursor.execute.assert_called_once()
    query, params = cursor.execute.call_args.args

    assert "FROM public.users" in query
    assert "WHERE id = %s" in query
    assert params == (7,)

    cursor.fetchone.assert_called_once_with()



def test_fetch_user_by_id_returns_none_when_not_found():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = fetch_user_by_id(999, pool)

    assert result is None

    query, params = cursor.execute.call_args.args

    assert "WHERE id = %s" in query
    assert params == (999,)

    cursor.fetchone.assert_called_once_with()



def test_fetch_user_by_id_closes_cursor_and_connection_contexts():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = {"id": 7}

    fetch_user_by_id(7, pool)

    pool.connection.return_value.__enter__.assert_called_once()
    pool.connection.return_value.__exit__.assert_called_once()

    connection.cursor.return_value.__enter__.assert_called_once()
    connection.cursor.return_value.__exit__.assert_called_once()



def test_fetch_user_by_id_propagates_database_error():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    cursor.execute.side_effect = Exception("Database error")

    with pytest.raises(Exception, match="Database error"):
        fetch_user_by_id(7, pool)



def test_post_user_returns_created_user():
    pool = MagicMock()

    fake_user = {
        "id": 7,
        "name": "Ana",
        "email": "ana@example.com",
        "role": "user",
        "telephone": "11999999999",
        "cpf": "12345678901",
        "is_active": True,
    }

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = fake_user

    result = post_user(
        pool,
        name="Ana",
        email="ana@example.com",
        password_hash="hashed_password",
        telephone="11999999999",
        cpf="12345678901",
    )

    assert result == fake_user

    cursor.execute.assert_called_once()
    query, params = cursor.execute.call_args.args

    assert "INSERT INTO users" in query
    assert "RETURNING" in query
    assert params == (
        "Ana",
        "ana@example.com",
        "hashed_password",
        "11999999999",
        "12345678901",
    )

    cursor.fetchone.assert_called_once_with()



def test_post_user_raises_error_when_email_already_exists():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    error = errors.UniqueViolation("Duplicate email")
    diagnostic = MagicMock()
    diagnostic.constraint_name = "users_email_key"

    with patch.object(
        errors.UniqueViolation,
        "diag",
        new_callable=PropertyMock,
        return_value=diagnostic,
    ):
        cursor.execute.side_effect = error

        with pytest.raises(
            UserEmailAlreadyExistsError,
            match="Este e-mail já está cadastrado.",
        ):
            post_user(
                pool,
                name="Ana",
                email="ana@example.com",
                password_hash="hashed_password",
                telephone="11999999999",
                cpf="12345678901",
            )



def test_post_user_raises_error_when_cpf_already_exists():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    error = errors.UniqueViolation("Duplicate CPF")
    diagnostic = MagicMock()
    diagnostic.constraint_name = "users_cpf_key"

    with patch.object(
        errors.UniqueViolation,
        "diag",
        new_callable=PropertyMock,
        return_value=diagnostic,
    ):
        cursor.execute.side_effect = error

        with pytest.raises(
            UserCPFAlreadyExistsError,
            match="Este CPF já está cadastrado.",
        ):
            post_user(
                pool,
                name="Ana",
                email="ana@example.com",
                password_hash="hashed_password",
                telephone="11999999999",
                cpf="12345678901",
            )



def test_post_user_propagates_unexpected_unique_violation():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    error = errors.UniqueViolation("Unexpected unique constraint")
    diagnostic = MagicMock()
    diagnostic.constraint_name = "users_unexpected_key"

    with patch.object(
        errors.UniqueViolation,
        "diag",
        new_callable=PropertyMock,
        return_value=diagnostic,
    ):
        cursor.execute.side_effect = error

        with pytest.raises(errors.UniqueViolation):
            post_user(
                pool,
                name="Ana",
                email="ana@example.com",
                password_hash="hashed_password",
                telephone="11999999999",
                cpf="12345678901",
            )



def test_put_user_rejects_empty_data():
    pool = MagicMock()

    with pytest.raises(
        ValueError,
        match="Nenhum campo informado para atualização.",
    ):
        put_user(pool, 7, {})

    pool.connection.assert_not_called()



def test_put_user_rejects_disallowed_fields():
    pool = MagicMock()

    with pytest.raises(
        ValueError,
        match="Campo não permitido para atualização.",
    ):
        put_user(pool, 7, {"role": "admin"})

    pool.connection.assert_not_called()



def test_put_user_updates_user_successfully():
    pool = MagicMock()

    fake_user = {
        "id": 7,
        "name": "Ana Silva",
        "email": "ana@example.com",
        "telephone": "11999999999",
    }

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = fake_user

    result = put_user(
        pool,
        7,
        {
            "name": "Ana Silva",
            "telephone": "11999999999",
        },
    )

    assert result == fake_user

    cursor.execute.assert_called_once()
    
    query, params = cursor.execute.call_args.args

    query_text = query.as_string()

    assert "UPDATE public.users" in query_text
    assert "RETURNING" in query_text
    assert params == ["Ana Silva", "11999999999", 7]

    cursor.fetchone.assert_called_once_with()



def test_put_user_returns_none_when_user_not_found():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value
    cursor.fetchone.return_value = None

    result = put_user(pool, 999, {"name": "Ana Silva"})

    assert result is None

    cursor.execute.assert_called_once()
    query, params = cursor.execute.call_args.args

    query_text = query.as_string()

    assert "UPDATE public.users" in query_text
    assert "WHERE id = %s" in query_text
    assert params == ["Ana Silva", 999]

    cursor.fetchone.assert_called_once_with()



def test_put_user_raises_error_when_email_already_exists():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    error = errors.UniqueViolation("Duplicate email")
    diagnostic = MagicMock()
    diagnostic.constraint_name = "users_email_key"

    with patch.object(
        errors.UniqueViolation,
        "diag",
        new_callable=PropertyMock,
        return_value=diagnostic,
    ):
        cursor.execute.side_effect = error

        with pytest.raises(
            UserEmailAlreadyExistsError,
            match="Este e-mail já está cadastrado.",
        ):
            put_user(pool, 7, {"email": "ana@example.com"})



def test_put_user_propagates_unexpected_unique_violation():
    pool = MagicMock()

    connection = pool.connection.return_value.__enter__.return_value
    cursor = connection.cursor.return_value.__enter__.return_value

    error = errors.UniqueViolation("Unexpected unique constraint")
    diagnostic = MagicMock()
    diagnostic.constraint_name = "users_unexpected_key"

    with patch.object(
        errors.UniqueViolation,
        "diag",
        new_callable=PropertyMock,
        return_value=diagnostic,
    ):
        cursor.execute.side_effect = error

        with pytest.raises(errors.UniqueViolation):
            put_user(pool, 7, {"email": "ana@example.com"})




