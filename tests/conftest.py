import os

os.environ["APP_ENV"] = "development"
os.environ["APP_DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-sessions"
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["AUTO_CREATE_TABLES"] = "true"
os.environ["APP_BASE_URL"] = "http://testserver"
os.environ["ADSENSE_ENABLED"] = "false"

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.main import app

get_settings.cache_clear()


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
