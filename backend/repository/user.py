from psycopg import errors, sql
from psycopg.rows import dict_row

from backend.app.exceptions import (
    UserEmailAlreadyExistsError,
    UserCPFAlreadyExistsError,
)


def fetch_users(pool, limit: int, offset: int):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    role,
                    telephone,
                    cpf,
                    is_active,
                    created_at,
                    updated_at
                FROM public.users
                ORDER BY id
                LIMIT %s OFFSET %s
                """,
                (limit, offset),
            )
            users = cursor.fetchall()

    return users


def fetch_user_by_id(
    id: int,
    pool
):
    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    email,
                    role,
                    telephone,
                    cpf,
                    is_active,
                    created_at,
                    updated_at
                FROM public.users
                WHERE id = %s
                """,
                (id,)
            )
            user = cursor.fetchone()

    return user


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


def put_user(pool, user_id: int, data: dict):
    
    allowed_fields = {"name", "email", "telephone"}

    if not data:
        raise ValueError("Nenhum campo informado para atualização.")

    if not set(data).issubset(allowed_fields):
        raise ValueError("Campo não permitido para atualização.")

    set_clause = sql.SQL(", ").join(
        sql.SQL("{} = %s").format(sql.Identifier(field))
        for field in data
    )

    query = sql.SQL("""
        UPDATE public.users
        SET {}
        WHERE id = %s
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
    """).format(set_clause)

    values = list(data.values())
    values.append(user_id)

    with pool.connection() as connection:
        with connection.cursor(row_factory=dict_row) as cursor:
            try:
                cursor.execute(query, values)
                user = cursor.fetchone()
            except errors.UniqueViolation as exc:
                if exc.diag.constraint_name == "users_email_key":
                    raise UserEmailAlreadyExistsError(
                    "Este e-mail já está cadastrado."
                    ) from exc
                raise
            
    return user
