import os
import sys
from pathlib import Path

import pytest



ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

# ============================================
# 1. 设置测试环境变量 (在导入app之前)
# ============================================
os.environ["ENVIRONMENT"] = "test"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///file:memdb?mode=memory&cache=shared&uri=true"
# os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./test_db.sqlite"
os.environ["SECRET_KEY"] = "test_secret_key_12345"
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["NEO4J_URI"] = "bolt://localhost:7687"
os.environ["NEO4J_USER"] = "neo4j"
os.environ["NEO4J_PASSWORD"] = "password"
os.environ["NEO4J_initial_dbms_default__database"] = "neo4j"

# ============================================
# 2. 导入应用和依赖
# ============================================
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import Settings
from src.app.models.base import Base
from src.app.core.database import DatabaseManager
from src.app.core.config import Settings
from src.app.core.security import create_access_token, get_password_hash
from src.app.main import app
from src.app.core.deps import get_db
from src.app.models.course import Course
from src.app.models.user import User
from src.app.models.enrollment import Enrollment
from src.app.models.quiz import Quiz

# --- 测试常量 ---
TEST_USER_NAME = "test user conf"
TEST_USER_EMAIL = "test.conf@example.com"
TEST_USER_PASSWORD = "a_very_secure_password_123@conf"
COURSE_ID = "existing_course"
COURSE_NAME = "Existing Course"


# --- Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def test_db_manager() -> DatabaseManager:
    """为测试创建独立的数据库管理器"""
    test_settings = Settings(ENVIRONMENT="test")
    test_db_mgr = DatabaseManager(test_settings)

    # 创建所有表
    from src.app.models import user, course, enrollment
    await test_db_mgr.create_all_tables(Base)

    yield test_db_mgr

    # 清理
    await test_db_mgr.drop_all_tables(Base)
    await test_db_mgr.close()


@pytest_asyncio.fixture(scope="function")
async def test_db(test_db_manager: DatabaseManager) -> AsyncGenerator[
    AsyncSession, None]:
    """提供测试数据库会话"""
    async with test_db_manager.get_session() as session:
        try:
            yield session
        finally:
            await session.close()


@pytest_asyncio.fixture(scope="function")
async def client(
        test_db: AsyncSession,
        test_db_manager: DatabaseManager
) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    del app.dependency_overrides[get_db]


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
    token = create_access_token(subject=str(user_in_db.id))
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def enrolled_user_client(
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course
):
    """提供一个已认证且其用户已注册了课程的客户端。"""
    new_enrollment = Enrollment(
        user_id=user_in_db.id,
        course_id=course_in_db.id
    )
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
