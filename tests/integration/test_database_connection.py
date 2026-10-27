def test_connection_uses_test_database(db_pool):
    with db_pool.connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_database()")
            database_name = cursor.fetchone()[0]

    assert database_name == "techere_test"