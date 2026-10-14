from psycopg import errors
from psycopg.rows import dict_row

from backend.app.exceptions import (
    UserEmailAlreadyExistsError,
    UserCPFAlreadyExistsError,
)


def post_user(
    pool,
    *,
    name: str,
    email: str,
    password_hash: str,
    telephone: str | None,
    cpf: str | None,
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            try:
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
                    ),
                )

                user = cursor.fetchone()

            except errors.UniqueViolation as exc:
                constraint = exc.diag.constraint_name

                if constraint == "users_email_key":
                    raise UserEmailAlreadyExistsError(
                        "Este e-mail já está cadastrado."
                    ) from exc

                if constraint == "users_cpf_key":
                    raise UserCPFAlreadyExistsError(
                        "Este CPF já está cadastrado."
                    ) from exc

                raise

    return user