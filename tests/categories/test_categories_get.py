from unittest.mock import patch

CATEGORY = {
    "id": 1,
    "name": "Periféricos",
}


def test_get_categories_success(client):
    with patch(
        "backend.app.api.routes.category.fetch_categories",
        return_value=[CATEGORY],
    ):
        response = client.get("/categories")

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == 1
    assert response.json()[0]["name"] == "Periféricos"


def test_get_category_by_id_success(client):
    with patch(
        "backend.app.api.routes.category.fetch_category_by_id",
        return_value=CATEGORY,
    ):
        response = client.get("/categories/1")

    assert response.status_code == 200
    assert response.json() == CATEGORY


def test_get_category_not_found(client):
    with patch(
        "backend.app.api.routes.category.fetch_category_by_id",
        return_value=None,
    ):
        response = client.get("/categories/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"
