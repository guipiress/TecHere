import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

connection = psycopg.connect(
    host=os.getenv("DB_HOST"),
    dbname=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    row_factory=dict_row
)


def fetch_products():
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM product")

    products = cursor.fetchall()
    
    cursor.close()

    return products


def fetch_product_by_id(id):
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM product WHERE id = %s",
                   (id,)
    )

    product = cursor.fetchone()

    cursor.close()

    return product


def post_product(name, purchase_price, sale_price, stock, brand, category_id, description):
    cursor = connection.cursor()

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

    connection.commit()
    cursor.close()
    
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

    


