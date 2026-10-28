from unittest.mock import patch

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


def test_get_products_success(client):
    with patch(
        "backend.app.api.routes.products.fetch_products",
        return_value=[PRODUCT],
    ):
        response = client.get("/products")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["name"] == "Teclado Mecânico"


def test_get_product_by_id_success(client):
    with patch(
        "backend.app.api.routes.products.fetch_product_by_id",
        return_value=PRODUCT,
    ):
        response = client.get("/products/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Teclado Mecânico"
    assert response.json()["category_name"] == "Periféricos"


def test_get_product_not_found(client):
    with patch(
        "backend.app.api.routes.products.fetch_product_by_id",
        return_value=None,
    ):
        response = client.get("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
