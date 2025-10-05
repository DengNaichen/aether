import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from app.schemas import StudentCreate
from src.app.main import app
from sqlalchemy.orm import sessionmaker

from src.app.models import Base
from src.app.crud import create_student
from src.app.database import get_db


# Use the memory database for testing
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
engine = create_async_engine(SQLALCHEMY_DATABASE_URL)


TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession
)


@pytest_asyncio.fixture(scope="function")
async def test_db():
    # create the sql database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


client = TestClient(app)


@pytest_asyncio.fixture(scope="function")
async def async_session(test_db):  # 这个 fixture 依赖于上面的 test_db fixture
    """
    为每个测试创建一个独立的数据库会话。
    """
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def registered_student(async_session: AsyncSession):
    """
    create a student in the database
    """
    student_password = "a_very_secure_password_123"
    student_data = StudentCreate(
        name='login_test_student',
        email='login.test@example.com',
        password=student_password
    )
    # await async_session.execute(create_student(student_data, db=async_session))
    create_student(student_data, db=async_session)
    return {"email": student_data.email, "password": student_password}


@pytest.mark.asyncio
async def test_login_success(test_db, registered_student):
    """
    Test login success with correct credentials
    """
    # client = TestClient(app)
    response = client.post(
        "/login",
        json={"email": registered_student["email"],
              "password": registered_student["password"]}
    )

    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    response_data = response.json()
    assert "access_token" in response_data
    assert response_data["token_type"] == "bearer"

