"""
Tests for Knowledge Node CRUD operations.

These tests verify node-related database operations:
- Node retrieval (by ID, by str_id, by graph)
- Node creation (single and bulk)
- Leaf node identification and queries
- Nodes without questions
"""

from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.knowledge_node import (
    # bulk_create_nodes,
    create_knowledge_node,
    get_node_by_id,
    get_node_by_str_id,
    get_nodes_by_graph,
)
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode  # Subtopic removed
from app.models.user import User


# ==================== Node Query Tests ====================
class TestGetNodeById:
    """Test cases for get_node_by_id function."""

    @pytest.mark.asyncio
    async def test_returns_node_when_exists(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return node when ID exists."""
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["derivatives"]

        result = await get_node_by_id(db_session=test_db, node_id=node.id)

        assert result is not None
        assert result.id == node.id
        assert result.node_name == node.node_name

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(self, test_db: AsyncSession):
        """Should return None when node does not exist."""
        nonexistent_id = uuid4()
        result = await get_node_by_id(db_session=test_db, node_id=nonexistent_id)

        assert result is None


class TestGetNodeByStrId:
    """Test cases for get_node_by_str_id function."""

    @pytest.mark.asyncio
    async def test_returns_node_when_str_id_exists(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return node when graph_id and node_id_str match."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Test", slug="test", description="Test"
        )
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(
            graph_id=graph.id,
            node_name="Test Node",
            node_id_str="test-node-123",
        )
        test_db.add(node)
        await test_db.commit()

        result = await get_node_by_str_id(
            db_session=test_db, graph_id=graph.id, node_id_str="test-node-123"
        )

        assert result is not None
        assert result.id == node.id
        assert result.node_id_str == "test-node-123"

    @pytest.mark.asyncio
    async def test_returns_none_when_str_id_not_found(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should return None when node_id_str does not exist."""
        result = await get_node_by_str_id(
            db_session=test_db,
            graph_id=private_graph_in_db.id,
            node_id_str="nonexistent",
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_when_graph_mismatch(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return None when node_id_str exists but graph_id doesn't match."""
        graph1 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 1", slug="graph-1")
        graph2 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 2", slug="graph-2")
        test_db.add_all([graph1, graph2])
        await test_db.flush()

        node = KnowledgeNode(
            graph_id=graph1.id,
            node_name="Node",
            node_id_str="shared-id",
        )
        test_db.add(node)
        await test_db.commit()

        # Search in graph2 (different graph)
        result = await get_node_by_str_id(
            db_session=test_db, graph_id=graph2.id, node_id_str="shared-id"
        )

        assert result is None


class TestGetNodesByGraph:
    """Test cases for get_nodes_by_graph function."""

    @pytest.mark.asyncio
    async def test_returns_all_nodes_in_graph(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return all nodes belonging to a graph."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        expected_nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        result = await get_nodes_by_graph(db_session=test_db, graph_id=graph.id)

        assert len(result) == len(expected_nodes)
        result_ids = {node.id for node in result}
        expected_ids = {node.id for node in expected_nodes.values()}
        assert result_ids == expected_ids

    @pytest.mark.asyncio
    async def test_empty_list_for_graph_without_nodes(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should return empty list for graph with no nodes."""
        result = await get_nodes_by_graph(
            db_session=test_db, graph_id=private_graph_in_db.id
        )

        assert result == []


# ==================== Node Creation Tests ====================
class TestCreateKnowledgeNode:
    """Test cases for create_knowledge_node function."""

    @pytest.mark.asyncio
    async def test_creates_node_with_required_fields(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should create node with only required fields."""
        node = await create_knowledge_node(
            db_session=test_db,
            graph_id=private_graph_in_db.id,
            node_name="Test Node",
        )

        assert node is not None
        assert node.id is not None
        assert node.graph_id == private_graph_in_db.id
        assert node.node_name == "Test Node"
        assert node.node_id_str is None
        assert node.description is None

    @pytest.mark.asyncio
    async def test_creates_node_with_all_fields(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should create node with all optional fields."""
        node = await create_knowledge_node(
            db_session=test_db,
            graph_id=private_graph_in_db.id,
            node_name="Complete Node",
            node_id_str="node-123",
            description="Test description",
        )

        assert node.node_id_str == "node-123"
        assert node.description == "Test description"

    @pytest.mark.asyncio
    async def test_node_is_committed(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should commit node to database."""
        node = await create_knowledge_node(
            db_session=test_db,
            graph_id=private_graph_in_db.id,
            node_name="Committed",
        )

        # Verify it persists
        result = await get_node_by_id(db_session=test_db, node_id=node.id)
        assert result is not None
        assert result.id == node.id
