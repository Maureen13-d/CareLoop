import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:  # context manager runs the lifespan (seeds data)
        yield c
