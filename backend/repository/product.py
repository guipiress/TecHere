from decimal import Decimal
from psycopg.rows import dict_row
from psycopg import errors
from backend.app.exceptions import CategoryNotFoundError, ProductConstraintError


def fetch_products(pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
             """SELECT
                    product.id,
                    product.name,
                    product.purchase_price,
                    product.sale_price,
                    product.stock,
                    product.brand,
                    product.category_id,
                    product.description,
                    category.name AS category_name
                FROM product
                INNER JOIN category
                    ON product.category_id = category.id;"""
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
                
             """SELECT 
                    product.id,
                    product.name,
                    product.purchase_price,
                    product.sale_price,
                    product.stock,
                    product.brand,
                    product.category_id,
                    product.description,
                    category.name AS category_name
                FROM product
                INNER JOIN category
                    ON product.category_id = category.id
                WHERE product.id = %s
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
                    INSERT INTO product (
                        name,
                        purchase_price,
                        sale_price,
                        stock,
                        brand,
                        category_id,
                        description
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
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
                product_id = product["id"]

                cursor.execute(
                    """
                    SELECT
                        product.id,
                        product.name,
                        product.purchase_price,
                        product.sale_price,
                        product.stock,
                        product.brand,
                        product.category_id,
                        product.description,
                        category.name AS category_name
                    FROM product
                    INNER JOIN category
                        ON product.category_id = category.id
                    WHERE product.id = %s
                    """,
                    (product_id,)
                )

                product = cursor.fetchone()

            except errors.ForeignKeyViolation:
                raise CategoryNotFoundError

            except errors.CheckViolation:
                raise ProductConstraintError

    return product



def put_product(pool, id: int, **data):
    allowed_fields = {
        "name",
        "purchase_price",
        "sale_price",
        "stock",
        "brand",
        "category_id",
        "description",
    }

    if not data:
        raise ValueError("At least one field must be provided")

    if not data.keys() <= allowed_fields:
        raise ValueError("Invalid product fields")

    from psycopg import sql

    fields = list(data.keys())

    query = sql.SQL("""
        UPDATE product
        SET {assignments}
        WHERE id = %s
        RETURNING id
    """).format(
        assignments=sql.SQL(", ").join(
            sql.SQL("{} = %s").format(sql.Identifier(field))
            for field in fields
        )
    )

    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            try:
                cursor.execute(
                    query,
                    (*[data[field] for field in fields], id),
                )
                result = cursor.fetchone()

                if result is None:
                    return None

                cursor.execute(
                    """
                    SELECT
                        product.id,
                        product.name,
                        product.purchase_price,
                        product.sale_price,
                        product.stock,
                        product.brand,
                        product.category_id,
                        product.description,
                        category.name AS category_name
                    FROM product
                    INNER JOIN category
                        ON product.category_id = category.id
                    WHERE product.id = %s
                    """,
                    (result["id"],),
                )
                return cursor.fetchone()

            except errors.ForeignKeyViolation:
                raise CategoryNotFoundError
            except errors.CheckViolation:
                raise ProductConstraintError



def del_product(
    pool,
    id: int
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    product.id,
                    product.name,
                    product.purchase_price,
                    product.sale_price,
                    product.stock,
                    product.brand,
                    product.category_id,
                    product.description,
                    category.name AS category_name
                FROM product
                INNER JOIN category
                    ON product.category_id = category.id
                WHERE product.id = %s
                """,
                (id,)
            )
            product = cursor.fetchone()
            if product is None:
                return None

            cursor.execute(
                """
                DELETE FROM product
                WHERE id = %s
                """,
                (id,)
            )

    return product