from unittest.mock import MagicMock

import pytest

from backend.app.exceptions import OrderConstraintError
from backend.repository.order import post_order


def test_post_order_rejects_duplicate_products():
    pool = MagicMock()

    items = [
        {"product_id": 1, "quantity": 2},
        {"product_id": 1, "quantity": 3},
    ]

    with pytest.raises(
        OrderConstraintError,
        match="A product cannot appear more than once in an order",
    ):
        post_order(
            pool,
            user_id=1,
            address_id=1,
            items=items,
        )

    pool.connection.assert_not_called()
