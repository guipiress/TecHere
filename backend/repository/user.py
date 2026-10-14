from psycopg.rows import dict_row


def post_user(
    pool,
    *,
    name: str,
    email: str,
    password_hash: str,
    telephone: str | None,
    cpf: str | None
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                    """
                    INSERT INTO users (
                    name,
                    email,
                    password_hash,
                    telephone,
                    cpf
                )
                VALUES (%s, %s, %s, %s, %s)
                RETURNING
                    id,
                    name,
                    email,
                    role,
                    telephone,
                    cpf,
                    is_active,
                    created_at,
                    updated_at
                """,
                (
                    name,
                    email,
                    password_hash,
                    telephone,
                    cpf,
                )
            )

            user = cursor.fetchone()
