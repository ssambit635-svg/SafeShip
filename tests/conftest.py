"""Pytest fixtures: TestClient and a fresh in-memory store per test."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import order_storage


@pytest.fixture
def client() -> TestClient:
    """Provide a TestClient with a fresh in-memory store for each test."""
    order_storage._orders.clear()
    with TestClient(app) as test_client:
        yield test_client
    order_storage._orders.clear()
