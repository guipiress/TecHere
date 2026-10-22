from unittest.mock import MagicMock, call
from backend.repository.user import fetch_users
import pytest


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
