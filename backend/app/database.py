from decimal import Decimal
from psycopg.rows import dict_row
from psycopg import errors
from backend.app.exceptions import CategoryNotFoundError, ProductConstraintError

def fetch_products(pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM product"
            )
            products = cursor.fetchall()

    return products


def fetch_product_by_id(
    id: int,
    pool
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM product
                WHERE id = %s
                """,
                (id,)
            )
            product = cursor.fetchone()

    return product


def post_product(
    pool,
    *,
    name: str,
    purchase_price: Decimal,
    sale_price: Decimal,
    stock: int,
    brand: str,
    category_id: int,
    description: str | None
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO product
                        (
                            name,
                            purchase_price,
                            sale_price,
                            stock,
                            brand,
                            category_id,
                            description
                        )
                    VALUES
                        (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING *
                    """,
                    (
                        name,
                        purchase_price,
                        sale_price,
                        stock,
                        brand,
                        category_id,
                        description
                    )
                )

                product = cursor.fetchone()

            except errors.ForeignKeyViolation:
                raise CategoryNotFoundError

            except errors.CheckViolation:
                raise ProductConstraintError

    return product


def create_category(
    pool,
    *,
    name: str
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            try:
                cursor.execute(
                    """
                    INSERT INTO category (name)
                    VALUES (%s)
                    RETURNING *
                    """,
                    (name,)
                )

                category = cursor.fetchone()

            except errors.UniqueViolation:
                raise

    return category


def put_product(
    pool,
    id: int,
    *,
    name: str,
    purchase_price: Decimal,
    sale_price: Decimal,
    stock: int,
    brand: str,
    category_id: int,
    description: str | None
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                UPDATE product
                SET
                    name = %s,
                    purchase_price = %s,
                    sale_price = %s,
                    stock = %s,
                    brand = %s,
                    category_id = %s,
                    description = %s
                WHERE id = %s
                RETURNING *
                """,
                (
                    name,
                    purchase_price,
                    sale_price,
                    stock,
                    brand,
                    category_id,
                    description,
                    id
                )
            )
            product = cursor.fetchone()

    return product


def del_product(
    pool,
    id: int
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                DELETE FROM product
                WHERE id = %s
                RETURNING *
                """,
                (id,)
            )
            product = cursor.fetchone()

    return product