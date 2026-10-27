from uuid import uuid4
from backend.repository.user import fetch_users, fetch_user_by_id, post_user, put_user, delete_user


def test_fetch_users_returns_user_from_database(db_pool):
    email = f"integration-{uuid4().hex}@example.com"
    user_id = None

    try:
        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.users (
                        name,
                        email,
                        password_hash
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    ("Integration Test User", email, "test-hash"),
                )
                user_id = cursor.fetchone()[0]

        users = fetch_users(db_pool, limit=100, offset=0)

        matching_users = [
            user for user in users
            if user["id"] == user_id
        ]

        assert len(matching_users) == 1
        assert matching_users[0]["email"] == email
        assert matching_users[0]["name"] == "Integration Test User"

    finally:
        if user_id is not None:
            with db_pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM public.users WHERE id = %s",
                        (user_id,),
                    )



def test_fetch_user_by_id_returns_user_from_database(db_pool):
    email = f"integration-{uuid4().hex}@example.com"
    user_id = None

    try:
        with db_pool.connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO public.users (
                        name,
                        email,
                        password_hash
                    )
                    VALUES (%s, %s, %s)
                    RETURNING id
                    """,
                    ("Integration Test User", email, "test-hash"),
                )
                user_id = cursor.fetchone()[0]

        user = fetch_user_by_id(user_id, db_pool)

        assert user is not None
        assert user["id"] == user_id
        assert user["email"] == email
        assert user["name"] == "Integration Test User"

    finally:
        if user_id is not None:
            with db_pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM public.users WHERE id = %s",
                        (user_id,),
                    )



def test_post_user_creates_user_in_database(db_pool):
    email = f"integration-{uuid4().hex}@example.com"
    user = None

    try:
        user = post_user(
            db_pool,
            name="Integration Test User",
            email=email,
            password_hash="test-hash",
            telephone=None,
            cpf=None,
        )

        assert user is not None
        assert user["id"] is not None
        assert user["email"] == email
        assert user["name"] == "Integration Test User"
        assert user["role"] == "CUSTOMER"
        assert user["is_active"] is True

        saved_user = fetch_user_by_id(user["id"], db_pool)

        assert saved_user is not None
        assert saved_user["email"] == email

    finally:
        if user is not None:
            with db_pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM public.users WHERE id = %s",
                        (user["id"],),
                    )



def test_put_user_updates_user_in_database(db_pool):
    email = f"integration-{uuid4().hex}@example.com"
    user = None

    try:
        user = post_user(
            db_pool,
            name="Integration Test User",
            email=email,
            password_hash="test-hash",
            telephone=None,
            cpf=None,
        )

        updated_user = put_user(
            db_pool,
            user["id"],
            {
                "name": "Updated Integration User",
                "telephone": "12999999999",
            },
        )

        assert updated_user is not None
        assert updated_user["id"] == user["id"]
        assert updated_user["name"] == "Updated Integration User"
        assert updated_user["telephone"] == "12999999999"

        saved_user = fetch_user_by_id(user["id"], db_pool)

        assert saved_user["name"] == "Updated Integration User"
        assert saved_user["telephone"] == "12999999999"

    finally:
        if user is not None:
            with db_pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM public.users WHERE id = %s",
                        (user["id"],),
                    )



def test_delete_user_removes_user_from_database(db_pool):
    email = f"integration-{uuid4().hex}@example.com"
    user = None

    try:
        user = post_user(
            db_pool,
            name="Integration Test User",
            email=email,
            password_hash="test-hash",
            telephone=None,
            cpf=None,
        )

        deleted_user = delete_user(db_pool, user["id"])

        assert deleted_user is not None
        assert deleted_user["id"] == user["id"]
        assert deleted_user["email"] == email

        remaining_user = fetch_user_by_id(user["id"], db_pool)

        assert remaining_user is None

    finally:
        if user is not None:
            with db_pool.connection() as connection:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "DELETE FROM public.users WHERE id = %s",
                        (user["id"],),
                    )
