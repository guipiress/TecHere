from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from backend.app.exceptions import (
    OrderConstraintError,
    ProductNotFoundError,
    InsufficientStockError,
    OrderNotFoundError,
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


def test_get_order_by_id_success(client):
    with patch(
        "backend.app.api.routes.orders.fetch_order_by_id",
        return_value=ORDER,
    ) as mock_fetch:
        response = client.get("/orders/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["items"][0]["product_id"] == 1
    mock_fetch.assert_called_once()


def test_get_order_by_id_not_found(client):
    with patch(
        "backend.app.api.routes.orders.fetch_order_by_id",
        side_effect=OrderNotFoundError,
    ):
        response = client.get("/orders/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


def test_get_order_by_id_invalid_id(client):
    response = client.get("/orders/abc")

    assert response.status_code == 422