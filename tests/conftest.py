import os
import pytest

# Use in-memory SQLite for tests so we don't touch a real DB file
@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    # use a test DB file so lifespan and request handlers share the same DB
    os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///./test_nivpro.db")
    os.environ.setdefault("SECRET_KEY", "test-secret-key")
    yield
