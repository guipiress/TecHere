from unittest.mock import patch

CATEGORY = {
    "id": 1,
    "name": "Periféricos",
}


def test_delete_category_success(client):
    with patch(
        "backend.app.api.routes.category.del_category",
        return_value=CATEGORY,
    ) as mock_delete:
        response = client.delete("/categories/1")

    assert response.status_code == 200
    assert response.json() == CATEGORY
    mock_delete.assert_called_once()


def test_delete_category_not_found(client):
    with patch(
        "backend.app.api.routes.category.del_category",
        return_value=None,
    ) as mock_delete:
        response = client.delete("/categories/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"
    mock_delete.assert_called_once()
