from backend.app.dependencies import get_current_user
from backend.app.main import app
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import patch


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


def test_get_orders_success(client):
    with patch(
        "backend.app.api.routes.orders.fetch_orders",
        return_value=[ORDER],
    ) as mock_fetch:
        response = client.get("/orders")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["items"][0]["product_id"] == 1
    assert mock_fetch.call_args.kwargs["user_id"] is None
    mock_fetch.assert_called_once()


def test_get_orders_empty(client):
    with patch(
        "backend.app.api.routes.orders.fetch_orders",
        return_value=[],
    ):
        response = client.get("/orders")

    assert response.status_code == 200
    assert response.json() == []


def test_customer_can_only_list_own_orders(client):
    customer = {
        "id": 42,
        "role": "CUSTOMER",
        "is_active": True,
    }

    app.dependency_overrides[get_current_user] = lambda: customer

    customer_order = {
        **ORDER,
        "user_id": 42,
    }

    with patch(
        "backend.app.api.routes.orders.fetch_orders",
        return_value=[customer_order],
    ) as mock_fetch:
        response = client.get("/orders")

    assert response.status_code == 200
    assert response.json()[0]["user_id"] == 42

    mock_fetch.assert_called_once()
    assert mock_fetch.call_args.kwargs["user_id"] == 42


def test_employee_can_list_all_orders(client):
    employee = {
        "id": 10,
        "role": "EMPLOYEE",
        "is_active": True,
    }

    app.dependency_overrides[get_current_user] = lambda: employee

    with patch(
        "backend.app.api.routes.orders.fetch_orders",
        return_value=[ORDER],
    ) as mock_fetch:
        response = client.get("/orders")

    assert response.status_code == 200
    assert len(response.json()) == 1

    mock_fetch.assert_called_once()
    assert mock_fetch.call_args.kwargs["user_id"] is None