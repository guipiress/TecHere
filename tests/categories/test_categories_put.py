from unittest.mock import patch

from psycopg import errors

CATEGORY = {
    "id": 1,
    "name": "Periféricos",
}


def test_update_category_success(client):
    updated_category = {
        "id": 1,
        "name": "Acessórios",
    }

    with patch(
        "backend.app.api.routes.category.put_category",
        return_value=updated_category,
    ) as mock_put:
        response = client.put(
            "/categories/1",
            json={"name": "Acessórios"},
        )

    assert response.status_code == 200
    assert response.json() == updated_category
    mock_put.assert_called_once_with(
        mock_put.call_args.args[0],
        1,
        name="Acessórios",
    )


def test_update_category_not_found(client):
    with patch(
        "backend.app.api.routes.category.put_category",
        return_value=None,
    ):
        response = client.put(
            "/categories/999",
            json={"name": "Acessórios"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Category not found"


def test_update_category_already_exists(client):
    with patch(
        "backend.app.api.routes.category.put_category",
        side_effect=errors.UniqueViolation("duplicate"),
    ):
        response = client.put(
            "/categories/1",
            json={"name": "Periféricos"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Category already exists"


def test_update_category_invalid_data(client):
    response = client.put(
        "/categories/1",
        json={"name": ""},
    )

    assert response.status_code == 422
