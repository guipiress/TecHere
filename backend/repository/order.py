from psycopg.rows import dict_row
from backend.app.exceptions import (
    OrderConstraintError,
    ProductNotFoundError,
    InsufficientStockError,
)


def post_order(pool, *, user_id: int, address_id: int, items: list[dict]):
    if not items:
        raise OrderConstraintError("Order must contain at least one item")

    product_ids = [item["product_id"] for item in items]

    if len(product_ids) != len(set(product_ids)):
        raise OrderConstraintError(
            "A product cannot appear more than once in an order"
        )

    with pool.connection() as connection:
        with connection.transaction():
            with connection.cursor(row_factory=dict_row) as cursor:
                cursor.execute(
                    """
                    SELECT id
                    FROM address
                    WHERE id = %s AND user_id = %s
                    """,
                    (address_id, user_id),
                )
                if cursor.fetchone() is None:
                    raise OrderConstraintError(
                        "Address not found or does not belong to user"
                    )

                total_price = 0
                validated_items = []

                for item in items:
                    cursor.execute(
                        """
                        SELECT id, sale_price, stock
                        FROM product
                        WHERE id = %s
                        FOR UPDATE
                        """,
                        (item["product_id"],),
                    )
                    product = cursor.fetchone()

                    if product is None:
                        raise ProductNotFoundError

                    if product["stock"] < item["quantity"]:
                        raise InsufficientStockError

                    unit_price = product["sale_price"]
                    total_price += unit_price * item["quantity"]

                    validated_items.append(
                        {
                            "product_id": product["id"],
                            "quantity": item["quantity"],
                            "unit_price": unit_price,
                        }
                    )

                cursor.execute(
                    """
                    INSERT INTO orders (
                        user_id, address_id, status, total_price
                    )
                    VALUES (%s, %s, 'PENDING', %s)
                    RETURNING id, user_id, address_id, status,
                              total_price, created_at
                    """,
                    (user_id, address_id, total_price),
                )
                order = cursor.fetchone()
                order_items = []

                for item in validated_items:
                    cursor.execute(
                        """
                        INSERT INTO order_items (
                            order_id, product_id, quantity, unit_price
                        )
                        VALUES (%s, %s, %s, %s)
                        RETURNING id, order_id, product_id,
                                  quantity, unit_price
                        """,
                        (
                            order["id"],
                            item["product_id"],
                            item["quantity"],
                            item["unit_price"],
                        ),
                    )
                    order_items.append(cursor.fetchone())

                    cursor.execute(
                        """
                        UPDATE product
                        SET stock = stock - %s
                        WHERE id = %s
                        """,
                        (item["quantity"], item["product_id"]),
                    )

                order["items"] = order_items

    return order



def fetch_orders(pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    o.id,
                    o.user_id,
                    o.address_id,
                    o.status,
                    o.total_price,
                    o.created_at,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', oi.id,
                                'order_id', oi.order_id,
                                'product_id', oi.product_id,
                                'quantity', oi.quantity,
                                'unit_price', oi.unit_price
                            )
                        ) FILTER (WHERE oi.id IS NOT NULL),
                        '[]'
                    ) AS items
                FROM orders o
                LEFT JOIN order_items oi
                    ON o.id = oi.order_id
                GROUP BY o.id
                ORDER BY o.created_at DESC;
                """
            )

            orders = cursor.fetchall()

    return orders
