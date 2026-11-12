"""Stock rows must be locked in a fixed order to avoid deadlocks."""
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from backend.app.exceptions import InsufficientStockError, ProductNotFoundError
from backend.repository.order import post_order


def _pool_with_cursor(cursor):
    pool = MagicMock()
    connection = pool.connection.return_value.__enter__.return_value
    connection.cursor.return_value.__enter__.return_value = cursor
    return pool


def _cursor(products):
    cursor = MagicMock()
    cursor.fetchone.side_effect = [
        {"id": 1},                                  # address check
        {"id": 10, "status": "PENDING",
         "total_price": Decimal("0")},              # inserted order
        {"id": 100, "order_id": 10, "product_id": 1,
         "quantity": 1, "unit_price": Decimal("1")},
        {"id": 101, "order_id": 10, "product_id": 2,
         "quantity": 1, "unit_price": Decimal("1")},
    ] * 3
    cursor.fetchall.return_value = products
    return cursor


def _statements(cursor):
    return [" ".join(c.args[0].split()) for c in cursor.execute.call_args_list]


def test_products_are_locked_in_one_ordered_statement():
    cursor = _cursor([
        {"id": 1, "sale_price": Decimal("1"), "stock": 5},
        {"id": 2, "sale_price": Decimal("1"), "stock": 5},
    ])
    pool = _pool_with_cursor(cursor)

    post_order(
        pool, user_id=1, address_id=1,
        items=[{"product_id": 2, "quantity": 1},
               {"product_id": 1, "quantity": 1}],
    )

    locks = [s for s in _statements(cursor) if "FROM product" in s and "FOR UPDATE" in s]
    assert len(locks) == 1
    assert "ORDER BY id" in locks[0]


def test_missing_product_is_reported():
    cursor = _cursor([{"id": 1, "sale_price": Decimal("1"), "stock": 5}])
    pool = _pool_with_cursor(cursor)

    with pytest.raises(ProductNotFoundError):
        post_order(
            pool, user_id=1, address_id=1,
            items=[{"product_id": 1, "quantity": 1},
                   {"product_id": 2, "quantity": 1}],
        )


def test_insufficient_stock_is_reported():
    cursor = _cursor([{"id": 1, "sale_price": Decimal("1"), "stock": 1}])
    pool = _pool_with_cursor(cursor)

    with pytest.raises(InsufficientStockError):
        post_order(
            pool, user_id=1, address_id=1,
            items=[{"product_id": 1, "quantity": 2}],
        )
