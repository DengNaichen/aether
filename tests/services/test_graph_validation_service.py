"""
Integration tests for GraphValidationService.

These tests verify the service layer's integration with:
- CRUD layer (database operations)
- Domain layer (graph algorithms)
- Complete end-to-end workflows
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode, Prerequisite  # Subtopic removed
from app.models.user import User
from app.services.graph_validation_service import GraphValidationService


# ==================== Cycle Detection Tests ====================
class TestDetectPrerequisiteCycle:
    """Test prerequisite cycle detection."""

    @pytest.mark.asyncio
    async def test_detects_simple_cycle(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should detect a simple 3-node cycle."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        n1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        n3 = KnowledgeNode(graph_id=graph.id, node_name="Node 3")
        test_db.add_all([n1, n2, n3])
        await test_db.flush()

        # Create cycle: n1 -> n2 -> n3
        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        p2 = Prerequisite(
            graph_id=graph.id, from_node_id=n2.id, to_node_id=n3.id, weight=1.0
        )
        test_db.add_all([p1, p2])
        await test_db.commit()

        service = GraphValidationService(test_db)

        # Adding n3 -> n1 would create cycle
        has_cycle = await service.detect_prerequisite_cycle(graph.id, n3.id, n1.id)
        assert has_cycle is True

        # Adding n1 -> n3 is safe (direct edge, no cycle)
        has_cycle = await service.detect_prerequisite_cycle(graph.id, n1.id, n3.id)
        assert has_cycle is False

    @pytest.mark.asyncio
    async def test_no_cycle_in_linear_chain(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should not detect cycle in a linear chain."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        n1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        n3 = KnowledgeNode(graph_id=graph.id, node_name="Node 3")
        test_db.add_all([n1, n2, n3])
        await test_db.flush()

        # Linear: n1 -> n2
        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        test_db.add(p1)
        await test_db.commit()

        service = GraphValidationService(test_db)

        # Adding n2 -> n3 is safe
        has_cycle = await service.detect_prerequisite_cycle(graph.id, n2.id, n3.id)
        assert has_cycle is False


class TestDetectSubtopicCycle:
    """Test subtopic hierarchy cycle detection."""

    # @pytest.mark.asyncio
    # async def test_detects_subtopic_cycle(
    #     self, test_db: AsyncSession, user_in_db: User
    # ):
    #     """Should detect cycle in subtopic hierarchy."""
    #     graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
    #     test_db.add(graph)
    #     await test_db.flush()

    #     parent = KnowledgeNode(graph_id=graph.id, node_name="Parent")
    #     child = KnowledgeNode(graph_id=graph.id, node_name="Child")
    #     grandchild = KnowledgeNode(graph_id=graph.id, node_name="Grandchild")
    #     test_db.add_all([parent, child, grandchild])
    #     await test_db.flush()

    #     # Hierarchy: parent -> child -> grandchild
    #     s1 = Subtopic(
    #         graph_id=graph.id,
    #         parent_node_id=parent.id,
    #         child_node_id=child.id,
    #         weight=1.0,
    #     )
    #     s2 = Subtopic(
    #         graph_id=graph.id,
    #         parent_node_id=child.id,
    #         child_node_id=grandchild.id,
    #         weight=1.0,
    #     )
    #     test_db.add_all([s1, s2])
    #     await test_db.commit()

    #     service = GraphValidationService(test_db)

    #     # Adding grandchild -> parent would create cycle
    #     has_cycle = await service.detect_subtopic_cycle(
    #         graph.id, grandchild.id, parent.id
    #     )
    #     assert has_cycle is True


# ==================== Topology Computation Tests ====================
class TestComputeTopologicalLevels:
    """Test topological level computation."""

    @pytest.mark.asyncio
    async def test_computes_levels_correctly(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should compute correct topological levels."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        # Create DAG: n1 -> n2 -> n3
        #             n1 -> n3
        n1 = KnowledgeNode(graph_id=graph.id, node_name="Foundation")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Intermediate")
        n3 = KnowledgeNode(graph_id=graph.id, node_name="Advanced")
        test_db.add_all([n1, n2, n3])
        await test_db.flush()

        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        p2 = Prerequisite(
            graph_id=graph.id, from_node_id=n2.id, to_node_id=n3.id, weight=1.0
        )
        test_db.add_all([p1, p2])
        await test_db.commit()

        service = GraphValidationService(test_db)
        levels = await service.compute_topological_levels(graph.id)

        assert levels[n1.id] == 0  # No prerequisites
        assert levels[n2.id] == 1  # Depends on n1
        assert levels[n3.id] == 2  # Depends on n2

    @pytest.mark.asyncio
    async def test_raises_on_cycle(self, test_db: AsyncSession, user_in_db: User):
        """Should raise ValueError if graph contains cycle."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        n1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([n1, n2])
        await test_db.flush()

        # Create cycle
        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        p2 = Prerequisite(
            graph_id=graph.id, from_node_id=n2.id, to_node_id=n1.id, weight=1.0
        )
        test_db.add_all([p1, p2])
        await test_db.commit()

        service = GraphValidationService(test_db)

        with pytest.raises(ValueError, match="cycle"):
            await service.compute_topological_levels(graph.id)


class TestComputeDependentsCount:
    """Test dependents count computation."""

    @pytest.mark.asyncio
    async def test_counts_dependents_correctly(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should count how many nodes depend on each node."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        # n1 is prerequisite for n2 and n3
        n1 = KnowledgeNode(graph_id=graph.id, node_name="Foundation")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Branch 1")
        n3 = KnowledgeNode(graph_id=graph.id, node_name="Branch 2")
        test_db.add_all([n1, n2, n3])
        await test_db.flush()

        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        p2 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n3.id, weight=1.0
        )
        test_db.add_all([p1, p2])
        await test_db.commit()

        service = GraphValidationService(test_db)
        dependents = await service.compute_dependents_count(graph.id)

        assert dependents[n1.id] == 2  # n2 and n3 depend on n1
        assert dependents[n2.id] == 0  # Nothing depends on n2
        assert dependents[n3.id] == 0  # Nothing depends on n3


# ==================== Batch Update Tests ====================
class TestUpdateGraphTopology:
    """Test end-to-end topology update."""

    @pytest.mark.asyncio
    async def test_updates_all_topology_metrics(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should update level and dependents_count for all nodes."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        n1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        n3 = KnowledgeNode(graph_id=graph.id, node_name="Node 3")
        test_db.add_all([n1, n2, n3])
        await test_db.flush()

        # Create chain: n1 -> n2 -> n3
        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        p2 = Prerequisite(
            graph_id=graph.id, from_node_id=n2.id, to_node_id=n3.id, weight=1.0
        )
        test_db.add_all([p1, p2])
        await test_db.commit()

        service = GraphValidationService(test_db)
        nodes_updated, max_level = await service.update_graph_topology(graph.id)

        assert nodes_updated == 3
        assert max_level == 2  # n3 is at level 2

        # Verify database was updated
        await test_db.refresh(n1)
        await test_db.refresh(n2)
        await test_db.refresh(n3)

        assert n1.level == 0
        assert n1.dependents_count == 1  # n2 depends on it

        assert n2.level == 1
        assert n2.dependents_count == 1  # n3 depends on it

        assert n3.level == 2
        assert n3.dependents_count == 0  # Nothing depends on it

    @pytest.mark.asyncio
    async def test_handles_empty_graph(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should handle empty graph gracefully."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Empty", slug="empty")
        test_db.add(graph)
        await test_db.commit()

        service = GraphValidationService(test_db)
        nodes_updated, max_level = await service.update_graph_topology(graph.id)

        assert nodes_updated == 0
        assert max_level == 0


# ==================== Validation Tests ====================
class TestValidateGraphStructure:
    """Test comprehensive graph validation."""

    @pytest.mark.asyncio
    async def test_valid_graph_passes(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return is_valid=True for valid graph."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        n1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([n1, n2])
        await test_db.flush()

        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        test_db.add(p1)
        await test_db.commit()

        service = GraphValidationService(test_db)
        report = await service.validate_graph_structure(graph.id)

        assert report["is_valid"] is True
        assert len(report["errors"]) == 0
        assert report["stats"]["node_count"] == 2
        assert report["stats"]["prerequisite_count"] == 1
        assert report["stats"]["max_level"] == 1

    @pytest.mark.asyncio
    async def test_detects_prerequisite_cycle(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should report error for prerequisite cycle."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        n1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([n1, n2])
        await test_db.flush()

        # Create cycle
        p1 = Prerequisite(
            graph_id=graph.id, from_node_id=n1.id, to_node_id=n2.id, weight=1.0
        )
        p2 = Prerequisite(
            graph_id=graph.id, from_node_id=n2.id, to_node_id=n1.id, weight=1.0
        )
        test_db.add_all([p1, p2])
        await test_db.commit()

        service = GraphValidationService(test_db)
        report = await service.validate_graph_structure(graph.id)

        assert report["is_valid"] is False
        assert len(report["errors"]) > 0
        assert any("cycle" in err.lower() for err in report["errors"])

    @pytest.mark.asyncio
    async def test_warns_about_orphaned_nodes(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should warn about nodes with no prerequisites."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        # Create isolated nodes
        n1 = KnowledgeNode(graph_id=graph.id, node_name="Isolated 1")
        n2 = KnowledgeNode(graph_id=graph.id, node_name="Isolated 2")
        test_db.add_all([n1, n2])
        await test_db.commit()

        service = GraphValidationService(test_db)
        report = await service.validate_graph_structure(graph.id)

        assert report["is_valid"] is True  # Not an error, just a warning
        assert len(report["warnings"]) > 0
        assert any("orphaned" in warn.lower() for warn in report["warnings"])

    @pytest.mark.asyncio
    async def test_includes_statistics(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should include comprehensive statistics in report."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        parent = KnowledgeNode(graph_id=graph.id, node_name="Parent")
        child = KnowledgeNode(graph_id=graph.id, node_name="Child")
        test_db.add_all([parent, child])
        await test_db.flush()

        # Add prerequisite and subtopic
        prereq = Prerequisite(
            graph_id=graph.id,
            from_node_id=child.id,
            to_node_id=parent.id,
            weight=1.0,
        )
        # subtopic = Subtopic(
        #     graph_id=graph.id,
        #     parent_node_id=parent.id,
        #     child_node_id=child.id,
        #     weight=1.0,
        # )
        test_db.add_all([prereq])
        await test_db.commit()

        service = GraphValidationService(test_db)
        report = await service.validate_graph_structure(graph.id)

        stats = report["stats"]
        assert stats["node_count"] == 2
        assert stats["prerequisite_count"] == 1
        # assert stats["subtopic_count"] == 1
        assert "max_level" in stats
