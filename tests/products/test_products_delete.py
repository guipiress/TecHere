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


def test_delete_product_success(client):
    with patch(
        "backend.app.api.routes.products.del_product",
        return_value=PRODUCT,
    ) as mock_delete:
        response = client.delete("/products/1")

    assert response.status_code == 200
    assert response.json()["id"] == 1
    assert response.json()["name"] == "Teclado Mecânico"
    mock_delete.assert_called_once()


def test_delete_product_not_found(client):
    with patch(
        "backend.app.api.routes.products.del_product",
        return_value=None,
    ) as mock_delete:
        response = client.delete("/products/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"
    mock_delete.assert_called_once()
