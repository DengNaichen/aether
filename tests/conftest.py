# import asyncio
import os
import sys
from datetime import datetime, timedelta

# import uuid
from pathlib import Path

from dotenv import load_dotenv
from jose import jwt

# Set ENVIRONMENT to 'test' BEFORE loading .env file
# This ensures Settings will load .env.test
os.environ["ENVIRONMENT"] = "test"

# Load test environment variables at the very beginning
# Use override=True to ensure test settings override any existing env vars
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env.test", override=True)

from redis.asyncio import Redis  # noqa: E402

ROOT_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT_DIR))

from collections.abc import AsyncGenerator  # noqa: E402
from typing import Any  # noqa: E402

# ============================================
# 2. import the dependency and app
# ============================================
import pytest_asyncio  # noqa: E402
from httpx import ASGITransport, AsyncClient  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

# from neo4j import AsyncGraphDatabase, AsyncDriver
from app.core.config import settings  # noqa: E402
from app.core.database import DatabaseManager  # noqa: E402
from app.core.deps import get_db, get_redis_client  # noqa: E402

# from app.core.security import create_access_token, get_password_hash
# Configure neomodel BEFORE importing app.main (which triggers lifespan)
# This ensures neomodel uses test database URL
# from neomodel import config as neomodel_config
# neomodel_config.DATABASE_URL = settings.NEOMODEL_NEO4J_URI
# print(f"🧪 Test neomodel configured with URI: {settings.NEO4J_URI}")
from app.main import app  # noqa: E402
from app.models.base import Base  # noqa: E402
from app.models.enrollment import GraphEnrollment  # noqa: E402
from app.models.knowledge_graph import KnowledgeGraph  # noqa: E402
from app.models.user import User  # noqa: E402
from app.schemas.knowledge_node import RelationType  # noqa: E402

# --- test constant ---
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
TEST_RELATION = RelationType.HAS_PREREQUISITES  # Changed from HAS_SUBTOPIC


def create_access_token(subject: Any, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token for testing purposes.
    Simulates a Supabase token.
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # Supabase tokens usually use "sub" for user ID
    to_encode = {
        "sub": str(subject),
        "exp": expire,
        "aud": "authenticated",
        "role": "authenticated",
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SUPABASE_JWT_SECRET, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


# --- Fixtures ---
@pytest_asyncio.fixture(scope="function")
async def test_db_manager() -> AsyncGenerator[DatabaseManager, Any]:
    """create a test database"""

    test_db_mgr = DatabaseManager(settings)

    await test_db_mgr.create_all_tables(Base)
    yield test_db_mgr
    await test_db_mgr.drop_all_tables(Base)
    await test_db_mgr.close()


@pytest_asyncio.fixture(scope="function")
async def test_db(
    test_db_manager: DatabaseManager,
) -> AsyncGenerator[AsyncSession, None]:
    """provide a database session for each test function, and clean after"""
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
async def client(
    test_db: AsyncSession, test_db_manager: DatabaseManager
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
    """create a user in the database"""
    new_user = User(
        email=TEST_USER_EMAIL,
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
        name=TEST_ADMIN_NAME,
        is_active=True,
        is_admin=True,
    )
    test_db.add(new_admin)
    await test_db.commit()
    await test_db.refresh(new_admin)
    return new_admin


@pytest_asyncio.fixture(scope="function")
async def other_user_in_db(test_db: AsyncSession) -> User:
    """Create a second regular user for testing non-owner access scenarios."""
    other_user = User(
        email="other.user@example.com",
        name="Other Test User",
        is_active=True,
    )
    test_db.add(other_user)
    await test_db.commit()
    await test_db.refresh(other_user)
    return other_user


@pytest_asyncio.fixture(scope="function")
async def private_graph_in_db(test_db: AsyncSession, user_in_db: User):
    new_graph = KnowledgeGraph(
        owner_id=user_in_db.id,
        name="Private Test Graph",
        slug="private-test-graph",
        description="This is a private knowledge graph for testing",
        tags=["test", "private"],
        is_public=False,
    )
    test_db.add(new_graph)
    await test_db.commit()
    await test_db.refresh(new_graph)
    return new_graph


@pytest_asyncio.fixture(scope="function")
async def private_graph_with_few_nodes_and_relations_in_db(
    test_db: AsyncSession,
    user_in_db: User,
):
    """
    Create a private knowledge graph with 5 nodes and various relationships.

    Graph structure:
        Node1 (Calculus Basics)
          ├─> Node2 (Derivatives) [SUBTOPIC]
          │    └─> Node4 (Chain Rule) [SUBTOPIC]
          └─> Node3 (Integrals) [SUBTOPIC]
               └─> Node5 (Integration by Parts) [SUBTOPIC]

        Node2 (Derivatives) ──[PREREQUISITE]──> Node3 (Integrals)
        Node4 (Chain Rule) ──[PREREQUISITE]──> Node5 (Integration by Parts)

    Returns:
        dict with:
            - graph: KnowledgeGraph object
            - nodes: dict mapping node_id to KnowledgeNode
            - prerequisites: list of Prerequisite relationships
            - subtopics: list of Subtopic relationships
    """
    from app.models.knowledge_node import KnowledgeNode, Prerequisite

    # Create the knowledge graph
    graph = KnowledgeGraph(
        owner_id=user_in_db.id,
        name="Calculus Learning Path",
        slug="calculus-learning-path",
        description="A structured path to learn calculus fundamentals",
        tags=["math", "calculus", "university"],
        is_public=False,
    )
    test_db.add(graph)
    await test_db.commit()
    await test_db.refresh(graph)

    # Create 5 nodes
    nodes_data = [
        {
            "key": "calculus-basics",  # Key for lookup in dict
            "node_name": "Calculus Basics",
            "description": "Fundamental concepts of calculus including limits and continuity",
        },
        {
            "key": "derivatives",
            "node_name": "Derivatives",
            "description": "Understanding rates of change and differentiation",
        },
        {
            "key": "integrals",
            "node_name": "Integrals",
            "description": "Integration and area under curves",
        },
        {
            "key": "chain-rule",
            "node_name": "Chain Rule",
            "description": "Advanced differentiation technique for composite functions",
        },
        {
            "key": "integration-by-parts",
            "node_name": "Integration by Parts",
            "description": "Advanced integration technique based on product rule",
        },
    ]

    nodes = {}
    for node_data in nodes_data:
        node = KnowledgeNode(
            graph_id=graph.id,
            node_name=node_data["node_name"],
            description=node_data["description"],
            level=0,  # Will be computed later
            dependents_count=0,
        )
        test_db.add(node)
        nodes[node_data["key"]] = node

    await test_db.commit()
    for node in nodes.values():
        await test_db.refresh(node)

    # Create Prerequisite relationships
    # Derivatives must be learned before Integrals
    # Chain Rule must be learned before Integration by Parts
    prerequisites_data = [
        {"from": "derivatives", "to": "integrals", "weight": 1.0},
        {"from": "chain-rule", "to": "integration-by-parts", "weight": 0.8},
    ]

    prerequisites = []
    for prereq_data in prerequisites_data:
        prereq = Prerequisite(
            graph_id=graph.id,
            from_node_id=nodes[prereq_data["from"]].id,
            to_node_id=nodes[prereq_data["to"]].id,
            weight=prereq_data["weight"],
        )
        test_db.add(prereq)
        prerequisites.append(prereq)

    await test_db.commit()
    for prereq in prerequisites:
        await test_db.refresh(prereq)

    # Subtopic relationships removed - using tags instead
    subtopics = []  # Keep empty list for backward compatibility

    return {
        "graph": graph,
        "nodes": nodes,
        "prerequisites": prerequisites,
        "subtopics": subtopics,  # Empty list
    }


@pytest_asyncio.fixture(scope="function")
async def graph_enrollment_owner_in_db(
    test_db: AsyncSession,
    user_in_db: User,
    private_graph_in_db: KnowledgeGraph,
) -> GraphEnrollment:
    """
    Owner enrolls in their own private graph to track learning progress.

    Use case: A teacher creates a personal curriculum and wants to track
    their own learning progress while developing it.

    Pattern: Private graphs can only be enrolled by their owner.
    """
    enrollment = GraphEnrollment(
        user_id=user_in_db.id,  # Owner enrolls in their own graph
        graph_id=private_graph_in_db.id,
        is_active=True,
    )
    test_db.add(enrollment)
    await test_db.commit()
    await test_db.refresh(enrollment)
    return enrollment


@pytest_asyncio.fixture(scope="function")
async def template_graph_in_db(
    test_db: AsyncSession,
    admin_in_db: User,
) -> KnowledgeGraph:
    """
    Create an official template graph that students can enroll in.

    Template graphs are:
    - Marked as template (is_template=True)
    - Immutable (should not be modified after students enroll)
    - Safe for multiple students to enroll
    - Usually created by admins

    Note: is_public is set to True for template graphs so they're visible.
    """
    template_graph = KnowledgeGraph(
        owner_id=admin_in_db.id,  # Created by admin
        name="Official Calculus Template",
        slug="official-calculus-template",
        description="Official curriculum template for calculus learning",
        tags=["template", "official", "calculus"],
        is_public=True,  # Visible to all
        is_template=True,  # Immutable, multi-user
    )
    test_db.add(template_graph)
    await test_db.commit()
    await test_db.refresh(template_graph)
    return template_graph


@pytest_asyncio.fixture(scope="function")
async def graph_enrollment_student_in_db(
    test_db: AsyncSession,
    user_in_db: User,  # Regular user acts as student
    template_graph_in_db: KnowledgeGraph,
) -> GraphEnrollment:
    """
    Student enrolls in an official template graph.

    Pattern:
    - Only template graphs (is_template=True) allow non-owner enrollment
    - Student's progress is tracked in UserMastery table
    - Template graph remains unchanged, safe for all learners
    """
    enrollment = GraphEnrollment(
        user_id=user_in_db.id,  # Student enrolls
        graph_id=template_graph_in_db.id,  # In a template graph
        is_active=True,
    )
    test_db.add(enrollment)
    await test_db.commit()
    await test_db.refresh(enrollment)
    return enrollment


@pytest_asyncio.fixture(scope="function")
async def question_in_db(test_db: AsyncSession, user_in_db: User):
    """
    Create a complete question with supporting graph and node in the test database.

    This fixture sets up the entire hierarchy needed for a valid question:
    - User (graph owner)
    - Knowledge Graph
    - Knowledge Node
    - Question

    Returns the Question object with all foreign keys satisfied.
    """
    from app.models.knowledge_node import KnowledgeNode
    from app.models.question import Question, QuestionDifficulty, QuestionType

    # Create the knowledge graph
    graph = KnowledgeGraph(
        owner_id=user_in_db.id,
        name="Test Graph for Questions",
        slug="test-graph-questions",
        description="Test graph for question fixtures",
    )
    test_db.add(graph)
    await test_db.flush()

    # Create the knowledge node
    node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Test Node",
        description="Test node for questions",
    )
    test_db.add(node)
    await test_db.flush()

    # Create the question with valid foreign keys
    question = Question(
        graph_id=graph.id,
        node_id=node.id,
        question_type=QuestionType.MULTIPLE_CHOICE.value,
        text="What is the capital of France?",
        details={
            "question_type": QuestionType.MULTIPLE_CHOICE.value,
            "options": ["London", "Paris", "Berlin"],
            "correct_answer": 1,
            "p_g": 0.33,
            "p_s": 0.1,
        },
        difficulty=QuestionDifficulty.EASY.value,
    )
    test_db.add(question)
    await test_db.commit()
    await test_db.refresh(question)
    return question


@pytest_asyncio.fixture(scope="function")
async def authenticated_client(client: AsyncClient, user_in_db: User) -> AsyncClient:
    token = create_access_token(user_in_db.id)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture(scope="function")
async def other_user_client(client: AsyncClient, other_user_in_db: User) -> AsyncClient:
    """Create an authenticated client for the second user (for testing non-owner access)."""
    token = create_access_token(other_user_in_db.id)
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def cleanup_test_db():
    """
    Clean the database after the test session
    """
    yield
    import os

    if os.path.exists("./test_db.sqlite"):
        os.remove("./test_db.sqlite")
