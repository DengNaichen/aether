import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from unittest.mock import MagicMock, AsyncMock

# ============================================
# 1. SET UP THE TEST ENVIRONMENT BEFORE APP IMPORT
# ============================================
# Set environment variables directly. This runs before any other code,
# including the app import, ensuring the settings are available globally.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["NEO4J_initial_dbms_default__database"] = "neo4j"
os.environ["SECRET_KEY"] = "test_secret_key"


@pytest.fixture(scope="session", autouse=True)
def mock_neo4j_driver_session(request):
    """
    Use a session-scoped monkeypatch to mock the Neo4j driver for the
    entire test session. This avoids ScopeMismatch errors.
    """
    from _pytest.monkeypatch import MonkeyPatch
    mp = MonkeyPatch()
    # This is a session-scoped monkeypatch, so we manually call .undo() at the end.
    request.addfinalizer(mp.undo)

    mock_driver = MagicMock()
    mock_driver.verify_connectivity = AsyncMock()
    mp.setattr(
        "neo4j.AsyncGraphDatabase.driver", lambda *args, **kwargs: mock_driver
    )


# ============================================
# 2. NOW, IMPORT THE APP AND DEFINE FIXTURES
#    The app will see the overridden environment variables from above.
# ============================================
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from httpx import AsyncClient, ASGITransport

from src.app.main import app
from src.app.models.base import Base
from src.app.models.course import Course
from src.app.models.user import User
from src.app.core.database import get_db, engine as main_engine
from src.app.core.security import get_password_hash

# --- Test User Constants ---
TEST_USER_EMAIL = "test@example.com"
TEST_USER_PASSWORD = "a_very_secure_password_123"

# Use the same engine for creating/dropping tables as the main app for consistency
test_engine = main_engine

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
    class_=AsyncSession
)


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """
    This is the core database fixture. It creates all tables,
    seeds necessary data, yields a session for the test to use,
    and then cleans up by dropping all tables.
    Using "scope=function" ensures every test gets a fresh database.
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        # Seed the database with a test user and course
        hashed_password = get_password_hash(TEST_USER_PASSWORD)
        test_user = User(email=TEST_USER_EMAIL, name="Test User", hashed_password=hashed_password)
        test_course = Course(id="g11_phys", name="G11 Physics")
        session.add(test_user)
        session.add(test_course)
        await session.commit()

        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """
    This fixture creates a test client for making API requests.
    It overrides the 'get_db' dependency to use our clean, seeded test database.
    """
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    del app.dependency_overrides[get_db]