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

print(fetch_products())

def fetch_product_byid(id):
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM product WHERE id = %s",
                   (id,)
    )

    product = cursor.fetchone()

    cursor.close

    return product
