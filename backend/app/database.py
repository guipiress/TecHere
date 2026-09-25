import os
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool


load_dotenv()


pool = ConnectionPool(
    conninfo=(
        f"host={os.getenv('DB_HOST')} "
        f"dbname={os.getenv('DB_NAME')} "
        f"user={os.getenv('DB_USER')} "
        f"password={os.getenv('DB_PASSWORD')} "
        f"port={os.getenv('DB_PORT')}"
    ),
    min_size=1,
    max_size=10
)


def fetch_products():
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT * FROM product")
            products = cursor.fetchall()

    return products


def fetch_product_by_id(id):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                "SELECT * FROM product WHERE id = %s",
                (id,)
            )
            product = cursor.fetchone()

    return product


def post_product(name, purchase_price, sale_price, stock, brand, category_id, description):
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


def put_product(id, name, purchase_price, sale_price, stock, brand, category_id, description):
    cursor = connection.cursor()

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
        cursor.close()
        return None
    
    connection.commit()
    cursor.close()

    return product


def del_product(id):
    cursor = connection.cursor()

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
        cursor.close()
        return None

    connection.commit()
    cursor.close()

    return product

    


