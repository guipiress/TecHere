"""Request validation hardening (no database needed)."""
from unittest.mock import patch

import pytest

USER = {
    "name": "Ana Teste",
    "email": "ana@example.com",
    "password": "senha-segura-123",
}
PRODUCT = {
    "name": "Notebook",
    "purchase_price": "100.00",
    "sale_price": "150.00",
    "stock": 5,
    "brand": "Acme",
    "category_id": 1,
}


def test_user_email_is_lowercased(client):
    with patch("backend.app.api.routes.users.post_user") as mock_post:
        mock_post.side_effect = RuntimeError("stop")
        with pytest.raises(RuntimeError):
            client.post("/users", json={**USER, "email": "Ana@Example.COM"})
    assert mock_post.call_args.kwargs["email"] == "ana@example.com"


@pytest.mark.parametrize("payload", [
    {**USER, "name": "   "},
    {**USER, "name": "a\u0000b"},
    {**USER, "password": "x" * 129},
    {**USER, "telephone": "<script>alert(1)</script>"},
    {**USER, "role": "ADMIN"},
])
def test_user_create_rejects_bad_input(client, payload):
    with patch("backend.app.api.routes.users.post_user") as mock_post:
        response = client.post("/users", json=payload)
    assert response.status_code == 422
    mock_post.assert_not_called()


@pytest.mark.parametrize("payload", [
    {**PRODUCT, "brand": "b" * 51},
    {**PRODUCT, "name": "  "},
    {**PRODUCT, "sale_price": "10.999"},
    {**PRODUCT, "sale_price": "100000000.00"},
    {**PRODUCT, "stock": 2_147_483_648},
    {**PRODUCT, "category_id": 2_147_483_648},
    {**PRODUCT, "unexpected": 1},
])
def test_product_create_rejects_bad_input(client, payload):
    with patch("backend.app.api.routes.products.post_product") as mock_post:
        response = client.post("/products", json=payload)
    assert response.status_code == 422
    mock_post.assert_not_called()


def test_product_update_rejects_null_for_required_field(client):
    with patch("backend.app.api.routes.products.put_product") as mock_put:
        response = client.put("/products/1", json={"name": None})
    assert response.status_code == 422
    mock_put.assert_not_called()


def _order(items):
    return {"user_id": 1, "address_id": 1, "items": items}


@pytest.mark.parametrize("payload", [
    _order([{"product_id": i, "quantity": 1} for i in range(1, 52)]),
    _order([{"product_id": 1, "quantity": 1001}]),
    _order([{"product_id": 2_147_483_648, "quantity": 1}]),
])
def test_order_create_rejects_bad_input(client, payload):
    with patch("backend.app.api.routes.orders.post_order") as mock_post:
        response = client.post("/orders", json=payload)
    assert response.status_code == 422
    mock_post.assert_not_called()


@pytest.mark.parametrize("path,target", [
    ("/products", "backend.app.api.routes.products.fetch_products"),
    ("/categories", "backend.app.api.routes.category.fetch_categories"),
    ("/orders", "backend.app.api.routes.orders.fetch_orders"),
])
def test_list_endpoints_are_paginated(client, path, target):
    with patch(target, return_value=[]) as mock_fetch:
        assert client.get(path).status_code == 200
        assert mock_fetch.call_args.args[1:] == (20, 0)

        assert client.get(path, params={"limit": 5, "offset": 10}).status_code == 200
        assert mock_fetch.call_args.args[1:] == (5, 10)

        assert client.get(path, params={"limit": 101}).status_code == 422
        assert client.get(path, params={"limit": 0}).status_code == 422
        assert client.get(path, params={"offset": -1}).status_code == 422
