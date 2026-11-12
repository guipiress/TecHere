"""Database errors must become clean HTTP errors that leak nothing."""
from unittest.mock import patch

import pytest
from psycopg import errors
from psycopg_pool import PoolTimeout

SECRET = "Key (email)=(secret@example.com) already exists"

CASES = [
    (errors.ForeignKeyViolation(SECRET), 409),
    (errors.UniqueViolation(SECRET), 409),
    (errors.CheckViolation(SECRET), 422),
    (errors.NotNullViolation(SECRET), 422),
    (errors.StringDataRightTruncation(SECRET), 422),
    (errors.NumericValueOutOfRange(SECRET), 422),
    (errors.DeadlockDetected(SECRET), 503),
    (errors.LockNotAvailable(SECRET), 503),
    (PoolTimeout(SECRET), 503),
]


@pytest.mark.parametrize("exc,expected", CASES)
def test_database_errors_are_translated(client, exc, expected):
    with patch(
        "backend.app.api.routes.products.fetch_products",
        side_effect=exc,
    ):
        response = client.get("/products")

    assert response.status_code == expected
    assert "secret@example.com" not in response.text
    assert set(response.json()) == {"detail"}


def test_deleting_a_referenced_category_returns_409(client):
    with patch(
        "backend.app.api.routes.category.del_category",
        side_effect=errors.ForeignKeyViolation(SECRET),
    ):
        response = client.delete("/categories/1")

    assert response.status_code == 409


def test_security_headers_are_present(client):
    response = client.get("/")
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Cache-Control"] == "no-store"
