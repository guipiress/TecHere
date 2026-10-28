from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from backend.app.exceptions import (
    OrderConstraintError,
    ProductNotFoundError,
    InsufficientStockError,
)


ORDER = {
    "id": 1,
    "user_id": 1,
    "address_id": 1,
    "status": "PENDING",
    "total_price": Decimal("499.80"),
    "created_at": datetime.now(timezone.utc),
    "items": [
        {
            "id": 1,
            "order_id": 1,
            "product_id": 1,
            "quantity": 2,
            "unit_price": Decimal("249.90"),
        }
    ],
}


def test_create_order_success(client):
    with patch(
        "backend.app.api.routes.orders.post_order",
        return_value=ORDER,
    ) as mock_post:
        response = client.post(
            "/orders",
            json={
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 2}
                ],
            },
        )

    assert response.status_code == 201
    assert response.json()["id"] == 1
    assert response.json()["status"] == "PENDING"
    assert response.json()["total_price"] == "499.80"
    assert len(response.json()["items"]) == 1

    mock_post.assert_called_once_with(
        mock_post.call_args.args[0],
        user_id=1,
        address_id=1,
        items=[{"product_id": 1, "quantity": 2}],
    )


def test_create_order_invalid_address(client):
    with patch(
        "backend.app.api.routes.orders.post_order",
        side_effect=OrderConstraintError(
            "Address not found or does not belong to user"
        ),
    ):
        response = client.post(
            "/orders",
            json={
                "user_id": 1,
                "address_id": 999,
                "items": [
                    {"product_id": 1, "quantity": 1}
                ],
            },
        )

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Address not found or does not belong to user"
    )


def test_create_order_product_not_found(client):
    with patch(
        "backend.app.api.routes.orders.post_order",
        side_effect=ProductNotFoundError(),
    ):
        response = client.post(
            "/orders",
            json={
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 999, "quantity": 1}
                ],
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_create_order_insufficient_stock(client):
    with patch(
        "backend.app.api.routes.orders.post_order",
        side_effect=InsufficientStockError(),
    ):
        response = client.post(
            "/orders",
            json={
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 100}
                ],
            },
        )

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "Insufficient stock for one or more products"
    )


def test_create_order_without_items(client):
    with patch(
        "backend.app.api.routes.orders.post_order",
    ) as mock_post:
        response = client.post(
            "/orders",
            json={
                "user_id": 1,
                "address_id": 1,
                "items": [],
            },
        )

    assert response.status_code == 422
    mock_post.assert_not_called()


def test_create_order_invalid_quantity(client):
    with patch(
        "backend.app.api.routes.orders.post_order",
    ) as mock_post:
        response = client.post(
            "/orders",
            json={
                "user_id": 1,
                "address_id": 1,
                "items": [
                    {"product_id": 1, "quantity": 0}
                ],
            },
        )

    assert response.status_code == 422
    mock_post.assert_not_called()
