from unittest.mock import MagicMock
import pytest
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies import get_pool, get_current_user
from backend.app.rate_limit import clear_login_limiters
from backend.app.security import create_access_token

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
    app.dependency_overrides[get_pool] = lambda: mock_pool

    app.dependency_overrides[get_current_user] = lambda: {
        "id": 1,
        "role": "ADMIN",
        "is_active": True,
    }

    try:
        with TestClient(app) as test_client:
            yield test_client
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
