import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.dependencies import get_pool


@pytest.fixture
def client():
    app.dependency_overrides[get_pool] = lambda: object()

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()