import os
import sys
from pathlib import Path

from redis.asyncio import Redis

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ============================================
# 1. 设置测试环境变量 (在导入app之前)
# ============================================
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = (
    "sqlite+aiosqlite:///file:memdb?mode=memory&cache=shared&uri=true"
)
# os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_db.sqlite"
os.environ["SECRET_KEY"] = "test_secret_key_12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["NEO4J_initial_dbms_default__database"] = "neo4j"
os.environ["REDIS_URL"] = "redis://localhost:6379/1"

from typing import AsyncGenerator, Any

# ============================================
# 2. 导入应用和依赖
# ============================================
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.database import DatabaseManager
from app.core.deps import get_db, get_redis_client
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.models.base import Base
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User

# --- 测试常量 ---
TEST_USER_NAME = "test user conf"
TEST_ADMIN_NAME = "test admin conf"
TEST_USER_EMAIL = "test.conf@example.com"
TEST_ADMIN_EMAIL = "test.admin@example.com"
TEST_USER_PASSWORD = "a_very_secure_password_123@conf"
TEST_ADMIN_PASSWORD = "admin_very_secure_password_123@conf"
COURSE_ID = "existing_course"
COURSE_NAME = "Existing Course"


# --- Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def test_db_manager() -> AsyncGenerator[DatabaseManager, Any]:
    """为测试创建独立的数据库管理器"""
    test_settings = Settings(ENVIRONMENT="test")
    test_db_mgr = DatabaseManager(test_settings)

    await test_db_mgr.create_all_tables(Base)

    yield test_db_mgr

    await test_db_mgr.drop_all_tables(Base)
    await test_db_mgr.close()


@pytest_asyncio.fixture(scope="function")
async def test_db(
    test_db_manager: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """提供测试数据库会话"""
    async with test_db_manager.get_sql_session() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def test_redis(
        test_db_manager: DatabaseManager,
) -> AsyncGenerator[Redis, None]:
    """
    provide a redis client for each test function, and clean after
    """
    redis_client = test_db_manager.redis_client
    yield redis_client

    await redis_client.flushall()


@pytest_asyncio.fixture(scope="function")
async def client(
    test_db: AsyncSession,
    test_db_manager: DatabaseManager
) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    async def override_get_redis_client() -> AsyncGenerator[Redis, None]:
        yield test_db_manager.redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis_client

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    del app.dependency_overrides[get_db]
    del app.dependency_overrides[get_redis_client]


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
async def admin_in_db(test_db: AsyncSession) -> User:
    new_admin = User(
        email=TEST_ADMIN_EMAIL,
        hashed_password=get_password_hash(TEST_ADMIN_PASSWORD),
        name=TEST_ADMIN_NAME,
        is_active=True,
        is_admin=True,
    )
    test_db.add(new_admin)
    await test_db.commit()
    await test_db.refresh(new_admin)
    return new_admin


@pytest_asyncio.fixture(scope="function")
async def course_in_db(test_db: AsyncSession) -> Course:
    new_course = Course(
        id=COURSE_ID,
        name=COURSE_NAME,
        description="This is an existing course for test",
    )
    test_db.add(new_course)
    await test_db.commit()
    await test_db.refresh(new_course)
    return new_course


@pytest_asyncio.fixture(scope="function")
async def enrollment_in_db(
        test_db: AsyncSession,
        user_in_db: User
) -> Enrollment:
    new_enrollment = Enrollment(
        user_id=user_in_db.id,
        course_id=COURSE_ID,
    )
    test_db.add(new_enrollment)
    await test_db.commit()
    await test_db.refresh(new_enrollment)
    return new_enrollment


# @pytest_asyncio.fixture(scope="function")
# async def active_quiz_in_db(test_db: AsyncSession) -> Quiz:
#     # TODO: need to consider this fixture
#     new_quiz = Quiz(
#         user_id=TEST_USER_EMAIL,
#         course_id=COURSE_ID,
#         question_num=5
#     )
#     test_db.add(new_quiz)
#     await test_db.commit()
#     await test_db.refresh(new_quiz)
#     return new_quiz


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(
        client: AsyncClient,
        user_in_db: User
) -> AsyncClient:
    token = create_access_token(user_in_db)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def authenticated_admin_client(client: AsyncClient,
                                     admin_in_db: User) -> AsyncClient:
    token = create_access_token(admin_in_db)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def enrolled_user_client(
    authenticated_client: AsyncClient,
    test_db: AsyncSession,
    user_in_db: User,
    course_in_db: Course,
):
    """提供一个已认证且其用户已注册了课程的客户端。"""
    new_enrollment = Enrollment(user_id=user_in_db.id, course_id=course_in_db.id)
    test_db.add(new_enrollment)
    await test_db.commit()
    yield authenticated_client

    await test_db.delete(new_enrollment)
    await test_db.commit()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_test_db():
    """测试会话结束后清理测试数据库文件"""
    yield
    import os

    if os.path.exists("./test_db.sqlite"):
        os.remove("./test_db.sqlite")
