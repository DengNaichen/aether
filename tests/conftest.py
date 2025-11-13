import asyncio
import os
import sys
import uuid
from pathlib import Path
from dotenv import load_dotenv

# Set ENVIRONMENT to 'test' BEFORE loading .env file
# This ensures Settings will load .env.test
os.environ["ENVIRONMENT"] = "test"

# Load test environment variables at the very beginning
# Use override=True to ensure test settings override any existing env vars
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.test", override=True)

from redis.asyncio import Redis

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from typing import AsyncGenerator, Any, List

# ============================================
# 2. 导入应用和依赖
# ============================================
import pytest_asyncio
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncGraphDatabase, AsyncDriver
from unittest.mock import MagicMock, AsyncMock
from fastapi import UploadFile

from app.core.config import Settings, settings
from app.core.database import DatabaseManager
from app.core.deps import get_db, get_redis_client, get_neo4j_driver
from app.core.security import create_access_token, get_password_hash

# Configure neomodel BEFORE importing app.main (which triggers lifespan)
# This ensures neomodel uses test database URL
from neomodel import config as neomodel_config
neomodel_config.DATABASE_URL = settings.NEOMODEL_NEO4J_URI
print(f"🧪 Test neomodel configured with URI: {settings.NEO4J_URI}")

from app.main import app
from app.models.base import Base
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
import app.models.neo4j_model as neo
from app.schemas.knowledge_node import RelationType
import app.schemas.questions as pydantic
from app.worker.handlers import _enroll_user_in_course_sync
from app.models.quiz import QuizAttempt, QuizStatus

# --- 测试常量 ---
TEST_USER_NAME = "test user conf"
TEST_ADMIN_NAME = "test admin conf"
TEST_USER_EMAIL = "test.conf@example.com"
TEST_ADMIN_EMAIL = "test.admin@example.com"
TEST_USER_PASSWORD = "a_very_secure_password_123@conf"
TEST_ADMIN_PASSWORD = "admin_very_secure_password_123@conf"
COURSE_ID_ONE = "existing_course_one"
COURSE_NAME_ONE = "Existing Course One"
COURSE_ID_TWO = "existing_course_two"
COURSE_NAME_TWO = "Existing Course Two"
TARGET_KNOWLEDGE_NODE_ID = "target_test_node"
TARGET_KNOWLEDGE_NODE_NAME = "target test node"
TARGET_KNOWLEDGE_NODE_DESCRIPTION = "target test node description"
SOURCE_KNOWLEDGE_NODE_ID = "source_test_node"
SOURCE_KNOWLEDGE_NODE_NAME = "source test node"
SOURCE_KNOWLEDGE_NODE_DESCRIPTION = "source test node description"
TEST_RELATION = RelationType.HAS_SUBTOPIC


# --- Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def test_db_manager() -> AsyncGenerator[DatabaseManager, Any]:
    """为测试创建独立的数据库管理器"""
    from app.core.config import settings
    test_db_mgr = DatabaseManager(settings)

    await test_db_mgr.create_all_tables(Base)

    try:
        async with test_db_mgr.get_neo4j_session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
    except Exception as e:
        print(f"Warning: Failed to clean Neo4j before test: {e}")

    yield test_db_mgr

    await test_db_mgr.drop_all_tables(Base)

    try:
        async with test_db_mgr.get_neo4j_session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
    except Exception as e:
        print(f"Warning: Failed to clean Neo4j after test: {e}")

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

    await redis_client.flushall()

    yield redis_client

    await redis_client.flushall()


@pytest_asyncio.fixture(scope="function")
async def neo4j_test_driver(
    test_db_manager: DatabaseManager,
) -> AsyncGenerator[AsyncDriver, None]:
    neo4j_driver = test_db_manager.neo4j_driver
    yield neo4j_driver

    async with test_db_manager.get_neo4j_session() as session:
        await session.run("MATCH (n) DETACH DELETE n")


@pytest_asyncio.fixture(scope="function")
async def client(
    test_db: AsyncSession,
    test_db_manager: DatabaseManager
) -> AsyncGenerator[AsyncClient, None]:
    def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield test_db

    async def override_get_redis_client() -> AsyncGenerator[Redis, None]:
        yield test_db_manager.redis_client

    async def override_get_neo4j_driver() -> AsyncGenerator[AsyncDriver, None]:
        yield test_db_manager.neo4j_driver

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis_client] = override_get_redis_client
    app.dependency_overrides[get_neo4j_driver] = override_get_neo4j_driver

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    del app.dependency_overrides[get_db]
    del app.dependency_overrides[get_redis_client]
    del app.dependency_overrides[get_neo4j_driver]


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
async def course_in_db(test_db: AsyncSession):
    new_course_1 = Course(
        id=COURSE_ID_ONE,
        name=COURSE_NAME_ONE,
        description="This is an existing course for test",
    )
    new_course_2 = Course(
        id=COURSE_ID_TWO,
        name=COURSE_NAME_TWO,
        description="This is an existing course for test",
    )
    test_db.add(new_course_1)
    test_db.add(new_course_2)
    await test_db.commit()
    await test_db.refresh(new_course_1)
    await test_db.refresh(new_course_2)
    return new_course_1, new_course_2


@pytest_asyncio.fixture(scope="function")
async def enrollment_in_db(
        test_db: AsyncSession,
        user_in_db: User
) -> Enrollment:
    new_enrollment = Enrollment(
        user_id=user_in_db.id,
        course_id=COURSE_ID_ONE,
    )
    test_db.add(new_enrollment)
    await test_db.commit()
    await test_db.refresh(new_enrollment)
    return new_enrollment


# todo: write a Attempt in db
@pytest_asyncio.fixture(scope="function")
async def quiz_in_db(
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: tuple[Course, Course],
) -> QuizAttempt:
    course_one, _ = course_in_db
    new_attempt = QuizAttempt(
        user_id=user_in_db.id,
        course_id=course_one.id,
        question_num=2,
        status=QuizStatus.IN_PROGRESS
    )
    test_db.add(new_attempt)
    await test_db.commit()
    await test_db.refresh(new_attempt)
    return new_attempt


@pytest_asyncio.fixture(scope="function")
async def course_in_neo4j_db(
        test_db_manager: DatabaseManager,
) -> AsyncGenerator[Course, Any]:
    course_obj = neo.Course(
        course_id=COURSE_ID_ONE,
        course_name=COURSE_NAME_ONE,
    )

    async with test_db_manager.neo4j_scoped_connection():
        await asyncio.to_thread(course_obj.save)

    yield course_obj


@pytest_asyncio.fixture(scope="function")
async def user_in_neo4j_db(
    test_db_manager: DatabaseManager,
    course_in_neo4j_db: neo.Course,
    user_in_db: User,
) -> AsyncGenerator[neo.User, Any]:

    enrolled_course_id = course_in_neo4j_db.course_id
    user_id = user_in_db.id
    user_name = user_in_db.name

    try:
        async with test_db_manager.neo4j_scoped_connection():
            user_node, create = await asyncio.to_thread(
                _enroll_user_in_course_sync,
                user_id=str(user_id),
                user_name=user_name,
                course_id=enrolled_course_id,
            )
        if user_node is None:
            raise RuntimeError

    except Exception as e:
        print(f"❌ Error in user_in_neo4j_db fixture: {e}")
    yield user_node


@pytest_asyncio.fixture(scope="function")
async def nodes_in_neo4j_db(
        test_db_manager: DatabaseManager,
        course_in_neo4j_db: neo.Course,
) -> AsyncGenerator[tuple[neo.KnowledgeNode, neo.KnowledgeNode], Any]:

    target_node_obj = neo.KnowledgeNode(
        node_id=TARGET_KNOWLEDGE_NODE_ID,
        node_name=TARGET_KNOWLEDGE_NODE_NAME,
    )

    source_node_obj = neo.KnowledgeNode(
        node_id=SOURCE_KNOWLEDGE_NODE_ID,
        node_name=SOURCE_KNOWLEDGE_NODE_NAME,
    )

    async with test_db_manager.neo4j_scoped_connection():

        await asyncio.to_thread(target_node_obj.save)
        await asyncio.to_thread(source_node_obj.save)

        # connect course with BELONGS_TO relationship
        await asyncio.to_thread(
            target_node_obj.course.connect, course_in_neo4j_db
        )
        await asyncio.to_thread(
            source_node_obj.course.connect, course_in_neo4j_db
        )

    yield target_node_obj, source_node_obj


@pytest_asyncio.fixture(scope="function")
async def questions_in_neo4j_db(
        test_db_manager: DatabaseManager,
        nodes_in_neo4j_db: tuple[neo.KnowledgeNode, neo.KnowledgeNode],
) -> AsyncGenerator[
    tuple[neo.MultipleChoice, neo.FillInBlank], Any
]:
    target_node, source_node = nodes_in_neo4j_db

    mcq_obj = neo.MultipleChoice(
        question_id=uuid.UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7"),
        text="Which of these is a 'target' node?",
        difficulty=pydantic.QuestionDifficulty.EASY.value,
        options=["Target", "Source", "Neither"],
        correct_answer=0,
    )
    fib_obj = neo.FillInBlank(
        question_id="8f14e45f-ceea-467a-9af0-fd3c2a1234ab",
        text="The source node name is ____.",
        difficulty=pydantic.QuestionDifficulty.EASY.value,
        expected_answer=[SOURCE_KNOWLEDGE_NODE_NAME],
    )
    async with test_db_manager.neo4j_scoped_connection():
        await asyncio.to_thread(mcq_obj.save)
        await asyncio.to_thread(fib_obj.save)

        await asyncio.to_thread(mcq_obj.knowledge_node.connect, target_node)
        await asyncio.to_thread(fib_obj.knowledge_node.connect, source_node)

    yield mcq_obj, fib_obj


@pytest_asyncio.fixture(scope="function")
async def knowledge_graph_in_neo4j_db(
        test_db_manager: DatabaseManager,
        course_in_neo4j_db: neo.Course,
) -> AsyncGenerator[dict, Any]:
    """
    Create a complete knowledge graph with hierarchical relationships.

    Structure:
        Parent Topic (parent_topic)
        ├── Subtopic A (subtopic_a) [weight: 0.6]
        │   └── Question: MCQ about Subtopic A (correct answer: 0)
        └── Subtopic B (subtopic_b) [weight: 0.4]
            └── Question: MCQ about Subtopic B (correct answer: 1)

    Prerequisites:
        Subtopic A is prerequisite for Subtopic B

    Returns:
        dict with nodes and questions for easy access
    """
    # Create parent topic node
    parent_node = neo.KnowledgeNode(
        node_id="parent_topic",
        node_name="Parent Topic",
    )

    # Create subtopic nodes
    subtopic_a = neo.KnowledgeNode(
        node_id="subtopic_a",
        node_name="Subtopic A",
    )

    subtopic_b = neo.KnowledgeNode(
        node_id="subtopic_b",
        node_name="Subtopic B",
    )

    # Create MCQ questions
    mcq_a = neo.MultipleChoice(
        question_id=uuid.UUID("7c9e6679-7425-40de-944b-e07fc1f90ae7"),
        text="Which answer is correct for Subtopic A?",
        difficulty=pydantic.QuestionDifficulty.EASY.value,
        options=["Answer A (Correct)", "Answer B", "Answer C"],
        correct_answer=0,  # First option is correct
    )

    mcq_b = neo.MultipleChoice(
        question_id=uuid.UUID("8f14e45f-ceea-467a-9af0-fd3c2a1234ab"),
        text="Which answer is correct for Subtopic B?",
        difficulty=pydantic.QuestionDifficulty.EASY.value,
        options=["Answer A", "Answer B (Correct)", "Answer C"],
        correct_answer=1,  # Second option is correct
    )

    async with test_db_manager.neo4j_scoped_connection():
        # Save all nodes
        await asyncio.to_thread(parent_node.save)
        await asyncio.to_thread(subtopic_a.save)
        await asyncio.to_thread(subtopic_b.save)
        await asyncio.to_thread(mcq_a.save)
        await asyncio.to_thread(mcq_b.save)

        # Connect nodes to course
        await asyncio.to_thread(parent_node.course.connect, course_in_neo4j_db)
        await asyncio.to_thread(subtopic_a.course.connect, course_in_neo4j_db)
        await asyncio.to_thread(subtopic_b.course.connect, course_in_neo4j_db)

        # Create HAS_SUBTOPIC relationships (parent -> children)
        await asyncio.to_thread(
            parent_node.subtopic.connect,
            subtopic_a,
            {'weight': 0.6}  # Subtopic A weight
        )
        await asyncio.to_thread(
            parent_node.subtopic.connect,
            subtopic_b,
            {'weight': 0.4}  # Subtopic B weight
        )

        # Create IS_PREREQUISITE_FOR relationship
        # subtopic_a is prerequisite for subtopic_b
        await asyncio.to_thread(
            subtopic_a.prerequisites.connect,
            subtopic_b
        )

        # Connect questions to knowledge nodes (TESTS relationship)
        await asyncio.to_thread(mcq_a.knowledge_node.connect, subtopic_a)
        await asyncio.to_thread(mcq_b.knowledge_node.connect, subtopic_b)

    yield {
        'parent_node': parent_node,
        'subtopic_a': subtopic_a,
        'subtopic_b': subtopic_b,
        'mcq_a': mcq_a,  # Question for subtopic A
        'mcq_b': mcq_b,  # Question for subtopic B
    }


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
    """
    Provide a client who already enrolled in a course, 
    and of course, authenticated.
    """
    course_one, _ = course_in_db
    new_enrollment = Enrollment(
        user_id=user_in_db.id,
        course_id=course_one.id
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
