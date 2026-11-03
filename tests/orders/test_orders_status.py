from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch

from backend.app.exceptions import (
    OrderNotFoundError,
    OrderConstraintError,
)


ORDER = {
    "id": 1,
    "user_id": 1,
    "address_id": 1,
    "status": "PAID",
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


def test_update_order_status_success(client):
    with patch(
        "backend.app.api.routes.orders.update_order_status",
        return_value=ORDER,
    ) as mock_update:
        response = client.put(
            "/orders/1/status",
            json={"status": "PAID"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "PAID"
    mock_update.assert_called_once()


def test_update_order_status_not_found(client):
    with patch(
        "backend.app.api.routes.orders.update_order_status",
        side_effect=OrderNotFoundError,
    ):
        response = client.put(
            "/orders/999/status",
            json={"status": "PAID"},
        )

    assert response.status_code == 404


def test_update_order_status_invalid_transition(client):
    with patch(
        "backend.app.api.routes.orders.update_order_status",
        side_effect=OrderConstraintError("Invalid status transition"),
    ):
        response = client.put(
            "/orders/1/status",
            json={"status": "PAID"},
        )

    assert response.status_code == 409


def test_update_order_status_invalid_value(client):
    response = client.put(
        "/orders/1/status",
        json={"status": "SHIPPED"},
    )

    assert response.status_code == 422