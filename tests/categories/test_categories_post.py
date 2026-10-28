from unittest.mock import patch

from psycopg import errors

CATEGORY = {
    "id": 1,
    "name": "Periféricos",
}


def test_create_category_success(client):
    with patch(
        "backend.app.api.routes.category.post_category",
        return_value=CATEGORY,
    ) as mock_post:
        response = client.post(
            "/categories",
            json={"name": "Periféricos"},
        )

    assert response.status_code == 201
    assert response.json() == CATEGORY
    mock_post.assert_called_once_with(
        mock_post.call_args.args[0],
        name="Periféricos",
    )


def test_create_category_already_exists(client):
    with patch(
        "backend.app.api.routes.category.post_category",
        side_effect=errors.UniqueViolation("duplicate"),
    ):
        response = client.post(
            "/categories",
            json={"name": "Periféricos"},
        )

    assert response.status_code == 409
    assert response.json()["detail"] == "Category already exists"


def test_create_category_invalid_data(client):
    response = client.post(
        "/categories",
        json={"name": ""},
    )

    assert response.status_code == 422
