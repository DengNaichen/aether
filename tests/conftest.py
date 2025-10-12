import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pytest_asyncio
from typing import AsyncGenerator

# ============================================
# 1. 设置测试环境变量 (在导入app之前)
# ============================================
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["SECRET_KEY"] = "test_secret_key"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["NEO4J_initial_dbms_default__database"] = "neo4j"

# ============================================
# 2. 导入应用和依赖
# ============================================
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from src.app.core.database import get_db, engine as main_engine
from src.app.core.security import create_access_token, get_password_hash
from src.app.main import app
from src.app.models.base import Base
from src.app.models.course import Course
from src.app.models.enrollment import Enrollment
from src.app.models.user import User

# --- 测试常量 ---
TEST_USER_NAME = "test user conf"
TEST_USER_EMAIL = "test.conf@example.com"
TEST_USER_PASSWORD = "a_very_secure_password_123@conf"
COURSE_ID = "existing_course"
COURSE_NAME = "Existing course"


# --- 测试数据库设置 ---
test_engine = main_engine
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=test_engine, class_=AsyncSession
)


# --- Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """为每个测试提供一个干净、隔离的数据库会话。"""
    # 显式导入所有模型，确保它们在 create_all 之前已注册
    from src.app.models import user, course, enrollment

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestingSessionLocal() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def user_in_db(test_db: AsyncSession) -> User:
    """在数据库中创建一个用户，并返回该用户对象。"""
    new_user = User(
        email=TEST_USER_EMAIL,
        hashed_password=get_password_hash(TEST_USER_PASSWORD),
        name=TEST_USER_NAME,
        is_active=True,
    )
    test_db.add(new_user)
    await test_db.commit()
    await test_db.refresh(new_user)
    return new_user


@pytest_asyncio.fixture(scope="function")
async def course_in_db(test_db: AsyncSession) -> Course:
    """在数据库中创建一个课程，并返回该课程对象。"""
    new_course = Course(
        id="existing_course",
        name="Existing course",
        description="This is an existing course for test",
    )
    test_db.add(new_course)
    await test_db.commit()
    await test_db.refresh(new_course)
    return new_course


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """提供一个配置了测试数据库的API客户端。"""
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    del app.dependency_overrides[get_db]


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, user_in_db: User) -> AsyncClient:
    """提供一个已认证的客户端，其用户身份来自 user_in_db fixture。"""
    token = create_access_token(subject=str(user_in_db.id))
    client.headers["Authorization"] = f"Bearer {token}"
    yield client
    del client.headers["Authorization"]


@pytest_asyncio.fixture(scope="function")
async def enrolled_user_client(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
    user_in_db: User,
    course_in_db: Course,
):
    """提供一个已认证且其用户已注册了课程的客户端。"""
    new_enrollment = Enrollment(
        user_id=user_in_db.id, course_id=course_in_db.id
    )
    test_db.add(new_enrollment)
    await test_db.commit()
    yield authenticated_client