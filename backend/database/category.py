from psycopg.rows import dict_row
from psycopg import errors
from backend.app.exceptions import CategoryNotFoundError, ProductConstraintError


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


def fetch_categories(pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("""
                SELECT *
                FROM category
            """)

            categories = cursor.fetchall()

    return categories


def fetch_category_by_id(id: int, pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT *
                FROM category
                WHERE id = %s
                """,
                (id,)
            )

            category = cursor.fetchone()

    return category


def put_category(pool, id: int, *, name: str):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            try:
                cursor.execute(
                    """
                    UPDATE category
                    SET name = %s
                    WHERE id = %s
                    RETURNING *
                    """,
                    (name, id)
                )

                category = cursor.fetchone()

            except errors.UniqueViolation:
                raise

    return category