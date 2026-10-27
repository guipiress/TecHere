import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env.test", override=True)


def test_connection_uses_test_database():
    connection_string = (
        f"host={os.environ['TEST_DB_HOST']} "
        f"dbname={os.environ['TEST_DB_NAME']} "
        f"user={os.environ['TEST_DB_USER']} "
        f"password={os.environ['TEST_DB_PASSWORD']} "
        f"port={os.environ['TEST_DB_PORT']}"
    )

    with psycopg.connect(connection_string) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database_name = cursor.fetchone()[0]

    assert database_name == "techere_test"
