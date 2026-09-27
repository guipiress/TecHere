import os
from dotenv import load_dotenv
from psycopg.rows import dict_row

load_dotenv()


def fetch_products(pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM product")
            products = cursor.fetchall()

    return products

def fetch_product_by_id(id, pool):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM product WHERE id = %s",
                (id,)
            )
            product = cursor.fetchone()

    return product


def post_product(pool, name, purchase_price, sale_price, stock, brand, category_id, description):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                INSERT INTO product
                (name, purchase_price, sale_price, stock, brand, category_id, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (name, purchase_price, sale_price, stock, brand, category_id, description)
            )
            product = cursor.fetchone()
            connection.commit()

    return product


def put_product(pool, id, name, purchase_price, sale_price, stock, brand, category_id, description):
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

            if product is None:
                connection.rollback()
                return None

            connection.commit()

    return product


def del_product(pool, id):
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

            if product is None:
                connection.rollback()
                return None

            connection.commit()

    return product
    


