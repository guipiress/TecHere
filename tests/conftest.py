from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.dependencies import get_pool


@pytest.fixture
def mock_pool():
    return MagicMock()


@pytest.fixture
def client(mock_pool):
    app.dependency_overrides[get_pool] = lambda: mock_pool

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
