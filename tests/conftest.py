from unittest.mock import MagicMock
import pytest
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")

from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.dependencies import get_pool, get_current_user

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