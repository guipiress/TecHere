import os
from pathlib import Path

import psycopg
import pytest
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env.test", override=True)


@pytest.fixture
def db_pool():
    connection_string = (
        f"host={os.environ['TEST_DB_HOST']} "
        f"dbname={os.environ['TEST_DB_NAME']} "
        f"user={os.environ['TEST_DB_USER']} "
        f"password={os.environ['TEST_DB_PASSWORD']} "
        f"port={os.environ['TEST_DB_PORT']}"
    )

    if os.environ["TEST_DB_NAME"] != "techere_test":
        pytest.fail("Os testes de integração devem usar techere_test.")

    with psycopg.connect(connection_string) as connection:
        database_name = connection.execute(
            "SELECT current_database()"
        ).fetchone()[0]

    if database_name != "techere_test":
        pytest.fail("Conexão direcionada a um banco inesperado.")

    with ConnectionPool(
        conninfo=connection_string,
        min_size=1,
        max_size=2,
    ) as pool:
        yield pool