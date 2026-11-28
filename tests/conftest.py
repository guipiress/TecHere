import os
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[1]

# A developer's real .env wins when it exists (load_dotenv never overrides
# variables that are already set)...
load_dotenv(PROJECT_ROOT / ".env")

# ...and these throw-away values make the unit tests runnable on a machine
# (or a CI job) that has no .env and no database. Nothing here connects to
# PostgreSQL: the pool is replaced by a mock in every unit test, and the
# integration tests (tests/integration) use their own .env.test.
os.environ.setdefault("SECRET_KEY", "unit-test-only-secret-key-" + "0" * 32)
for _name, _value in {
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "unused-in-unit-tests",
    "DB_USER": "unused",
    "DB_PASSWORD": "unused",
}.items():
    os.environ.setdefault(_name, _value)

from fastapi.testclient import TestClient  # noqa: E402
from backend.app.main import app  # noqa: E402
from backend.app.dependencies import get_pool, get_current_user  # noqa: E402
from backend.app.rate_limit import clear_login_limiters  # noqa: E402
from backend.app.security import create_access_token  # noqa: E402


@pytest.fixture(autouse=True)
def reset_login_limiters():
    # The limiters are process-wide; without this, failed logins recorded by
    # one test would block the next one.
    clear_login_limiters()
    yield
    clear_login_limiters()


@pytest.fixture
def mock_pool():
    return MagicMock()


@pytest.fixture
def client(mock_pool):
    """Authenticated as an ADMIN, database mocked.

    TestClient is deliberately NOT used as a context manager: that would run
    the app's lifespan and open a real connection pool, making every unit test
    depend on a running PostgreSQL.
    """
    app.dependency_overrides[get_pool] = lambda: mock_pool

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "role": "ADMIN",
        "is_active": True,
    }

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def anonymous_client(mock_pool):
    """A client where get_current_user is NOT overridden.

    Real bearer-token validation and role checks run; only the database pool
    is replaced. Tests patch backend.app.dependencies.fetch_user_by_id to
    decide who the token's owner "is".
    """
    app.dependency_overrides[get_pool] = lambda: mock_pool

    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def bearer():
    """Build an Authorization header carrying a valid token for a user id."""

    def _bearer(user_id: int = 5) -> dict:
        token = create_access_token({"sub": str(user_id)})
        return {"Authorization": f"Bearer {token}"}

    return _bearer
