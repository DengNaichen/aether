"""
Tests for Prerequisite relationship CRUD operations.

These tests verify prerequisite relationship operations:
- Creating prerequisite relationships
- Leaf node validation for prerequisites
- Querying prerequisites by graph
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.prerequisite import create_prerequisite, get_prerequisites_by_graph
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode  # Subtopic removed
from app.models.user import User


# ==================== Prerequisite Creation Tests ====================
class TestCreatePrerequisite:
    """Test cases for create_prerequisite function."""

    @pytest.mark.asyncio
    async def test_creates_prerequisite_between_leaf_nodes(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create prerequisite when both nodes are leaves."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        # Create two leaf nodes (no children)
        leaf1 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 1")
        leaf2 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 2")
        test_db.add_all([leaf1, leaf2])
        await test_db.commit()

        # Create prerequisite
        prereq = await create_prerequisite(
            db_session=test_db,
            graph_id=graph.id,
            from_node_id=leaf1.id,
            to_node_id=leaf2.id,
            weight=1.0,
        )

        assert prereq is not None
        assert prereq.graph_id == graph.id
        assert prereq.from_node_id == leaf1.id
        assert prereq.to_node_id == leaf2.id
        assert prereq.weight == 1.0

    @pytest.mark.asyncio
    async def test_creates_prerequisite_with_custom_weight(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should create prerequisite with custom weight value."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        leaf1 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 1")
        leaf2 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 2")
        test_db.add_all([leaf1, leaf2])
        await test_db.commit()

        prereq = await create_prerequisite(
            db_session=test_db,
            graph_id=graph.id,
            from_node_id=leaf1.id,
            to_node_id=leaf2.id,
            weight=0.75,
        )

        assert prereq.weight == 0.75

    @pytest.mark.asyncio
    async def test_prerequisite_is_committed(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should commit prerequisite to database."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        leaf1 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 1")
        leaf2 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 2")
        test_db.add_all([leaf1, leaf2])
        await test_db.commit()

        await create_prerequisite(
            db_session=test_db,
            graph_id=graph.id,
            from_node_id=leaf1.id,
            to_node_id=leaf2.id,
        )

        # Verify it persists
        prereqs = await get_prerequisites_by_graph(test_db, graph.id)
        assert len(prereqs) == 1


# ==================== Prerequisite Query Tests ====================
class TestGetPrerequisitesByGraph:
    """Test cases for get_prerequisites_by_graph function."""

    @pytest.mark.asyncio
    async def test_returns_all_prerequisites_in_graph(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return all prerequisite relationships in a graph."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        expected_prereqs = private_graph_with_few_nodes_and_relations_in_db[
            "prerequisites"
        ]

        result = await get_prerequisites_by_graph(db_session=test_db, graph_id=graph.id)

        assert len(result) == len(expected_prereqs)
        result_ids = {(p.from_node_id, p.to_node_id) for p in result}
        expected_ids = {(p.from_node_id, p.to_node_id) for p in expected_prereqs}
        assert result_ids == expected_ids

    @pytest.mark.asyncio
    async def test_returns_empty_for_graph_without_prerequisites(
        self, test_db: AsyncSession, private_graph_in_db: KnowledgeGraph
    ):
        """Should return empty list for graph with no prerequisites."""
        result = await get_prerequisites_by_graph(
            db_session=test_db, graph_id=private_graph_in_db.id
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_includes_weight_information(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should include weight information for each prerequisite."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        leaf1 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 1")
        leaf2 = KnowledgeNode(graph_id=graph.id, node_name="Leaf 2")
        test_db.add_all([leaf1, leaf2])
        await test_db.commit()

        await create_prerequisite(
            db_session=test_db,
            graph_id=graph.id,
            from_node_id=leaf1.id,
            to_node_id=leaf2.id,
            weight=0.85,
        )

        result = await get_prerequisites_by_graph(db_session=test_db, graph_id=graph.id)

        assert len(result) == 1
        assert result[0].weight == 0.85

    @pytest.mark.asyncio
    async def test_only_returns_prerequisites_from_specified_graph(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should not return prerequisites from other graphs."""
        # Create two graphs
        graph1 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 1", slug="graph-1")
        graph2 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 2", slug="graph-2")
        test_db.add_all([graph1, graph2])
        await test_db.flush()

        # Create nodes in graph1
        node1_g1 = KnowledgeNode(graph_id=graph1.id, node_name="Node 1")
        node2_g1 = KnowledgeNode(graph_id=graph1.id, node_name="Node 2")
        test_db.add_all([node1_g1, node2_g1])
        await test_db.flush()

        # Create prerequisite in graph1
        await create_prerequisite(test_db, graph1.id, node1_g1.id, node2_g1.id)

        # Query graph2
        result = await get_prerequisites_by_graph(
            db_session=test_db, graph_id=graph2.id
        )

        # Should not include prerequisites from graph1
        assert result == []
