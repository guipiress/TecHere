from decimal import Decimal
from uuid import uuid4

import pytest

from backend.repository.order import (
    post_order,
    update_order_status,
)
from backend.app.exceptions import OrderConstraintError


def test_order_cancellation_restores_stock(db_pool):
    unique_id = uuid4().hex

    user_id = None
    address_id = None
    category_id = None
    product_id = None
    order_id = None

    try:
        with db_pool.connection() as connection:
            with connection.cursor() as cursor:

                cursor.execute(
                    """
                    INSERT INTO users (
                        name, email, password_hash
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        "Integration Order User",
                        f"{unique_id}@example.com",
                        "test-hash",
                    ),
                )
                user_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO address (
                        user_id, street, street_number,
                        district, city, state, zip_code, country
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        user_id,
                        "Test Street",
                        "100",
                        "Test District",
                        "Taubate",
                        "SP",
                        "12000000",
                        "BR",
                    ),
                )
                address_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO category (name)
                    VALUES (%s)
                    RETURNING id;
                    """,
                    (f"Integration-{unique_id}",),
                )
                category_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO product (
                        name, purchase_price, sale_price,
                        stock, brand, category_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        "Integration Test Product",
                        100.00,
                        150.00,
                        10,
                        "Test Brand",
                        category_id,
                    ),
                )
                product_id = cursor.fetchone()[0]

        order = post_order(
            db_pool,
            user_id=user_id,
            address_id=address_id,
            items=[
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ],
        )

        order_id = order["id"]

        assert order["status"] == "PENDING"
        assert order["total_price"] == 300.00

        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT stock FROM product WHERE id = %s",
                    (product_id,),
                )
                assert cursor.fetchone()[0] == 8

        cancelled_order = update_order_status(
            db_pool,
            order_id,
            "CANCELLED",
        )

        assert cancelled_order["status"] == "CANCELLED"

        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT stock FROM product WHERE id = %s",
                    (product_id,),
                )
                assert cursor.fetchone()[0] == 10

        with pytest.raises(OrderConstraintError):
            update_order_status(
                db_pool,
                order_id,
                "CANCELLED",
            )

        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT stock FROM product WHERE id = %s",
                    (product_id,),
                )
                assert cursor.fetchone()[0] == 10

    finally:
        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                if order_id is not None:
                    cursor.execute(
                        "DELETE FROM order_items WHERE order_id = %s",
                        (order_id,),
                    )
                    cursor.execute(
                        "DELETE FROM orders WHERE id = %s",
                        (order_id,),
                    )

                if product_id is not None:
                    cursor.execute(
                        "DELETE FROM product WHERE id = %s",
                        (product_id,),
                    )

                if category_id is not None:
                    cursor.execute(
                        "DELETE FROM category WHERE id = %s",
                        (category_id,),
                    )

                if address_id is not None:
                    cursor.execute(
                        "DELETE FROM address WHERE id = %s",
                        (address_id,),
                    )

                if user_id is not None:
                    cursor.execute(
                        "DELETE FROM users WHERE id = %s",
                        (user_id,),
                    )



def test_order_payment_keeps_stock_reduced(db_pool):
    unique_id = uuid4().hex

    user_id = None
    address_id = None
    category_id = None
    product_id = None
    order_id = None

    try:
        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO users (name, email, password_hash)
                    VALUES (%s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        "Integration Payment User",
                        f"{unique_id}@example.com",
                        "test-hash",
                    ),
                )
                user_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO address (
                        user_id, street, street_number,
                        district, city, state, zip_code, country
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        user_id, "Test Street", "100",
                        "Test District", "Taubate", "SP",
                        "12000000", "BR",
                    ),
                )
                address_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO category (name)
                    VALUES (%s)
                    RETURNING id;
                    """,
                    (f"Payment-{unique_id}",),
                )
                category_id = cursor.fetchone()[0]

                cursor.execute(
                    """
                    INSERT INTO product (
                        name, purchase_price, sale_price,
                        stock, brand, category_id
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        "Payment Test Product",
                        100.00, 150.00, 10,
                        "Test Brand", category_id,
                    ),
                )
                product_id = cursor.fetchone()[0]

        order = post_order(
            db_pool,
            user_id=user_id,
            address_id=address_id,
            items=[
                {
                    "product_id": product_id,
                    "quantity": 2,
                }
            ],
        )

        order_id = order["id"]

        assert order["status"] == "PENDING"
        assert order["total_price"] == Decimal("300.00")

        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT stock FROM product WHERE id = %s",
                    (product_id,),
                )
                assert cursor.fetchone()[0] == 8

        paid_order = update_order_status(
            db_pool,
            order_id,
            "PAID",
        )

        assert paid_order["status"] == "PAID"

        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT stock FROM product WHERE id = %s",
                    (product_id,),
                )
                assert cursor.fetchone()[0] == 8

                cursor.execute(
                    "SELECT status FROM orders WHERE id = %s",
                    (order_id,),
                )
                assert cursor.fetchone()[0] == "PAID"

    finally:
        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                if order_id is not None:
                    cursor.execute(
                        "DELETE FROM order_items WHERE order_id = %s",
                        (order_id,),
                    )
                    cursor.execute(
                        "DELETE FROM orders WHERE id = %s",
                        (order_id,),
                    )

                if product_id is not None:
                    cursor.execute(
                        "DELETE FROM product WHERE id = %s",
                        (product_id,),
                    )

                if category_id is not None:
                    cursor.execute(
                        "DELETE FROM category WHERE id = %s",
                        (category_id,),
                    )

                if address_id is not None:
                    cursor.execute(
                        "DELETE FROM address WHERE id = %s",
                        (address_id,),
                    )

                if user_id is not None:
                    cursor.execute(
                        "DELETE FROM users WHERE id = %s",
                        (user_id,),
                    )
