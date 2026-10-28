from unittest.mock import patch

from backend.app.exceptions import (
    CategoryNotFoundError,
)

PRODUCT = {
    "id": 1,
    "name": "Teclado Mecânico",
    "purchase_price": "150.00",
    "sale_price": "249.90",
    "stock": 10,
    "brand": "Logitech",
    "category_id": 1,
    "category_name": "Periféricos",
    "description": "Teclado mecânico para jogos",
}


def test_update_product_success(client):
    with patch(
        "backend.app.api.routes.products.put_product",
        return_value={**PRODUCT, "stock": 20},
    ) as mock_put:
        response = client.put(
            "/products/1",
            json={"stock": 20},
        )

    assert response.status_code == 200
    assert response.json()["stock"] == 20
    mock_put.assert_called_once_with(
        mock_put.call_args.args[0],
        1,
        stock=20,
    )


def test_update_product_not_found(client):
    with patch(
        "backend.app.api.routes.products.put_product",
        return_value=None,
    ):
        response = client.put(
            "/products/999",
            json={"stock": 20},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"


def test_update_product_without_fields(client):
    with patch(
        "backend.app.api.routes.products.put_product",
    ) as mock_put:
        response = client.put("/products/1", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "At least one field must be provided"
    )
    mock_put.assert_not_called()


def test_update_product_category_not_found(client):
    with patch(
        "backend.app.api.routes.products.put_product",
        side_effect=CategoryNotFoundError,
    ):
        response = client.put(
            "/products/1",
            json={"category_id": 999},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"



def test_update_product_invalid_data(client):
    response = client.put(
        "/products/1",
        json={"stock": -1},
    )

    assert response.status_code == 422
