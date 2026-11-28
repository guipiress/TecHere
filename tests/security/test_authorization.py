"""Authentication and role checks, with real tokens and real role logic.

The default `client` fixture replaces get_current_user with an ADMIN, so it
cannot prove that a route is protected. These tests use `anonymous_client`
instead: only the database is faked.
"""

from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import jwt
import pytest

from backend.app.security import ALGORITHM, SECRET_KEY, create_access_token

FETCH_USER = "backend.app.dependencies.fetch_user_by_id"
NOW = datetime(2026, 1, 1, tzinfo=timezone.utc)


def make_user(role="CUSTOMER", user_id=5, active=True):
    return {
        "id": user_id,
        "name": "Fulano",
        "email": "fulano@example.com",
        "role": role,
        "telephone": None,
        "cpf": None,
        "is_active": active,
        "created_at": NOW,
        "updated_at": NOW,
    }


PRODUCT_BODY = {
    "name": "Teclado",
    "purchase_price": "100.00",
    "sale_price": "150.00",
    "stock": 5,
    "brand": "Acme",
    "category_id": 1,
}
PRODUCT_ROW = {
    "id": 1,
    "name": "Teclado",
    "purchase_price": "100.00",
    "sale_price": "150.00",
    "stock": 5,
    "brand": "Acme",
    "category_id": 1,
    "category_name": "Periféricos",
    "description": None,
}
CATEGORY_ROW = {"id": 1, "name": "Periféricos"}
ORDER_BODY = {"address_id": 1, "items": [{"product_id": 1, "quantity": 1}]}

# (method, path, json body)
PROTECTED = [
    ("POST", "/products", PRODUCT_BODY),
    ("PUT", "/products/1", {"stock": 1}),
    ("DELETE", "/products/1", None),
    ("POST", "/categories", {"name": "Nova"}),
    ("PUT", "/categories/1", {"name": "Outra"}),
    ("DELETE", "/categories/1", None),
    ("GET", "/users", None),
    ("GET", "/users/me", None),
    ("GET", "/users/1", None),
    ("PUT", "/users/1", {"name": "X"}),
    ("DELETE", "/users/1", None),
    ("GET", "/orders", None),
    ("GET", "/orders/1", None),
    ("POST", "/orders", ORDER_BODY),
    ("PUT", "/orders/1/status", {"status": "PAID"}),
]


def call(client, method, path, body=None, headers=None):
    return client.request(method, path, json=body, headers=headers)


def as_role(client, bearer, role, method, path, body=None, user_id=5):
    with patch(FETCH_USER, return_value=make_user(role, user_id)):
        return call(client, method, path, body, bearer(user_id))


# --- no / bad credentials ----------------------------------------------------

@pytest.mark.parametrize("method,path,body", PROTECTED)
def test_protected_routes_reject_requests_without_a_token(
    anonymous_client, method, path, body
):
    response = call(anonymous_client, method, path, body)

    assert response.status_code == 401
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_malformed_authorization_header_is_rejected(anonymous_client):
    response = anonymous_client.get(
        "/orders", headers={"Authorization": "Token abc"}
    )

    assert response.status_code == 401


def test_expired_token_is_rejected(anonymous_client):
    token = jwt.encode(
        {"sub": "5", "exp": datetime.now(timezone.utc) - timedelta(days=1)},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )

    with patch(FETCH_USER, return_value=make_user("ADMIN")):
        response = anonymous_client.get(
            "/users", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401


def test_token_signed_with_another_key_is_rejected(anonymous_client):
    token = jwt.encode(
        {"sub": "5", "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        "a-different-secret-key-with-32-bytes!!",
        algorithm=ALGORITHM,
    )

    with patch(FETCH_USER, return_value=make_user("ADMIN")):
        response = anonymous_client.get(
            "/users", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401


def test_token_without_expiry_is_rejected(anonymous_client):
    token = jwt.encode({"sub": "5"}, SECRET_KEY, algorithm=ALGORITHM)

    with patch(FETCH_USER, return_value=make_user("ADMIN")):
        response = anonymous_client.get(
            "/users", headers={"Authorization": f"Bearer {token}"}
        )

    assert response.status_code == 401


def test_deactivated_user_loses_access_immediately(anonymous_client, bearer):
    # The token is still valid and unexpired; the account state is what counts.
    with patch(FETCH_USER, return_value=make_user("ADMIN", active=False)):
        response = anonymous_client.get("/users", headers=bearer(5))

    assert response.status_code == 401


def test_deleted_user_token_is_rejected(anonymous_client, bearer):
    with patch(FETCH_USER, return_value=None):
        response = anonymous_client.get("/users/me", headers=bearer(5))

    assert response.status_code == 401


def test_role_comes_from_the_database_not_from_the_token(
    anonymous_client, bearer
):
    headers = bearer(5)  # the very same token in both calls

    with patch(FETCH_USER, return_value=make_user("CUSTOMER")):
        assert anonymous_client.get("/users", headers=headers).status_code == 403

    with patch("backend.app.api.routes.users.fetch_users", return_value=[]):
        with patch(FETCH_USER, return_value=make_user("ADMIN")):
            assert anonymous_client.get("/users", headers=headers).status_code == 200


# --- customers ----------------------------------------------------------------

@pytest.mark.parametrize(
    "method,path,body",
    [
        ("POST", "/products", PRODUCT_BODY),
        ("PUT", "/products/1", {"stock": 1}),
        ("DELETE", "/products/1", None),
        ("POST", "/categories", {"name": "Nova"}),
        ("PUT", "/categories/1", {"name": "Outra"}),
        ("DELETE", "/categories/1", None),
        ("GET", "/users", None),
        ("GET", "/users/1", None),           # somebody else's profile
        ("PUT", "/users/1", {"name": "X"}),  # somebody else's profile
        ("DELETE", "/users/5", None),        # not even their own
        ("PUT", "/orders/1/status", {"status": "PAID"}),
    ],
)
def test_customer_is_forbidden(anonymous_client, bearer, method, path, body):
    response = as_role(anonymous_client, bearer, "CUSTOMER", method, path, body)

    assert response.status_code == 403


def test_customer_can_read_and_edit_their_own_profile(anonymous_client, bearer):
    me = make_user("CUSTOMER", 5)

    with patch(FETCH_USER, return_value=me):
        assert anonymous_client.get("/users/me", headers=bearer(5)).json()["id"] == 5

        with patch(
            "backend.app.api.routes.users.fetch_user_by_id", return_value=me
        ):
            assert anonymous_client.get("/users/5", headers=bearer(5)).status_code == 200

        with patch("backend.app.api.routes.users.put_user", return_value=me):
            response = anonymous_client.put(
                "/users/5", json={"name": "Novo Nome"}, headers=bearer(5)
            )

    assert response.status_code == 200


def test_customer_cannot_change_their_own_email(anonymous_client, bearer):
    with patch("backend.app.api.routes.users.put_user") as mock_put:
        response = as_role(
            anonymous_client, bearer, "CUSTOMER", "PUT", "/users/5",
            {"email": "attacker@example.com"},
        )

    assert response.status_code == 403
    mock_put.assert_not_called()


def test_admin_can_change_a_users_email(anonymous_client, bearer):
    target = make_user("CUSTOMER", 9)

    with patch("backend.app.api.routes.users.put_user", return_value=target):
        response = as_role(
            anonymous_client, bearer, "ADMIN", "PUT", "/users/9",
            {"email": "new@example.com"}, user_id=1,
        )

    assert response.status_code == 200


# --- staff ---------------------------------------------------------------------

def test_employee_can_create_and_update_the_catalogue(anonymous_client, bearer):
    with patch("backend.app.api.routes.products.post_product", return_value=PRODUCT_ROW):
        r = as_role(anonymous_client, bearer, "EMPLOYEE", "POST", "/products", PRODUCT_BODY)
    assert r.status_code == 201

    with patch("backend.app.api.routes.products.put_product", return_value=PRODUCT_ROW):
        r = as_role(anonymous_client, bearer, "EMPLOYEE", "PUT", "/products/1", {"stock": 3})
    assert r.status_code == 200

    with patch("backend.app.api.routes.category.post_category", return_value=CATEGORY_ROW):
        r = as_role(anonymous_client, bearer, "EMPLOYEE", "POST", "/categories", {"name": "Nova"})
    assert r.status_code == 201


@pytest.mark.parametrize(
    "path",
    ["/products/1", "/categories/1", "/users/1"],
)
def test_employee_cannot_delete(anonymous_client, bearer, path):
    response = as_role(anonymous_client, bearer, "EMPLOYEE", "DELETE", path)

    assert response.status_code == 403


def test_employee_cannot_list_users(anonymous_client, bearer):
    response = as_role(anonymous_client, bearer, "EMPLOYEE", "GET", "/users")

    assert response.status_code == 403


def test_admin_can_delete_a_product(anonymous_client, bearer):
    with patch("backend.app.api.routes.products.del_product", return_value=PRODUCT_ROW):
        response = as_role(anonymous_client, bearer, "ADMIN", "DELETE", "/products/1")

    assert response.status_code == 200


# --- orders: ownership fails closed ------------------------------------------

@pytest.mark.parametrize("role,expected_scope", [
    ("CUSTOMER", 5),
    ("SUPPLIER", 5),     # a role that does not exist yet must NOT see everything
    ("EMPLOYEE", None),
    ("ADMIN", None),
])
def test_order_listing_scope_by_role(anonymous_client, bearer, role, expected_scope):
    with patch("backend.app.api.routes.orders.fetch_orders", return_value=[]) as mock_fetch:
        response = as_role(anonymous_client, bearer, role, "GET", "/orders")

    assert response.status_code == 200
    assert mock_fetch.call_args.kwargs["user_id"] == expected_scope


def test_the_buyer_comes_from_the_token_not_the_body(anonymous_client, bearer):
    # user_id in the body is not even an accepted field any more.
    body = {**ORDER_BODY, "user_id": 999}

    with patch("backend.app.api.routes.orders.post_order") as mock_post:
        response = as_role(anonymous_client, bearer, "CUSTOMER", "POST", "/orders", body)

    assert response.status_code == 422
    mock_post.assert_not_called()


# --- public surface ------------------------------------------------------------

def test_public_catalogue_hides_the_purchase_price(anonymous_client):
    with patch("backend.app.api.routes.products.fetch_products", return_value=[PRODUCT_ROW]):
        listing = anonymous_client.get("/products")

    with patch("backend.app.api.routes.products.fetch_product_by_id", return_value=PRODUCT_ROW):
        single = anonymous_client.get("/products/1")

    assert listing.status_code == 200 and single.status_code == 200
    assert "purchase_price" not in listing.json()[0]
    assert "purchase_price" not in single.json()


def test_staff_responses_still_include_the_purchase_price(anonymous_client, bearer):
    with patch("backend.app.api.routes.products.post_product", return_value=PRODUCT_ROW):
        response = as_role(anonymous_client, bearer, "ADMIN", "POST", "/products", PRODUCT_BODY)

    assert response.json()["purchase_price"] == "100.00"


def test_categories_are_public_to_read(anonymous_client):
    with patch("backend.app.api.routes.category.fetch_categories", return_value=[CATEGORY_ROW]):
        assert anonymous_client.get("/categories").status_code == 200


def test_signup_is_public_and_cannot_choose_a_role(anonymous_client):
    body = {"name": "Novo", "email": "novo@example.com", "password": "SenhaForte123!"}

    with patch("backend.app.api.routes.users.post_user", return_value=make_user()):
        assert anonymous_client.post("/users", json=body).status_code == 201

    with patch("backend.app.api.routes.users.post_user") as mock_post:
        response = anonymous_client.post("/users", json={**body, "role": "ADMIN"})

    assert response.status_code == 422
    mock_post.assert_not_called()


def test_signup_is_rate_limited_per_address(anonymous_client):
    body = {"name": "Novo", "email": "novo@example.com", "password": "SenhaForte123!"}

    with patch("backend.app.api.routes.users.hash_password", return_value="h"):
        with patch("backend.app.api.routes.users.post_user", return_value=make_user()):
            for _ in range(10):
                assert anonymous_client.post("/users", json=body).status_code == 201

            response = anonymous_client.post("/users", json=body)

    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0
