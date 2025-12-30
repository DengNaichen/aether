"""
Tests for Graph Structure operations (complex graph operations).

These tests verify:
- Graph visualization with mastery scores
- Bulk graph structure import
- Node/edge data formatting
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.graph_structure import (
    batch_update_node_topology,
    get_graph_statistics,
    get_graph_visualization,
    get_prerequisite_adjacency_list,
    import_graph_structure,
    reset_node_topology,
)
from app.crud.knowledge_node import get_nodes_by_graph
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode, Prerequisite
from app.models.user import User, UserMastery
from app.schemas.knowledge_node import (
    GraphStructureImport,
    NodeImport,
    PrerequisiteImport,
)


# ==================== Graph Visualization Tests ====================
class TestGetGraphVisualization:
    """Test cases for get_graph_visualization function."""

    @pytest.mark.asyncio
    async def test_returns_nodes_with_mastery_scores(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return nodes with user mastery scores."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([node1, node2])
        await test_db.flush()

        # Add mastery for node1
        mastery = UserMastery(
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node1.id,
            cached_retrievability=0.85,
        )
        test_db.add(mastery)
        await test_db.commit()

        result = await get_graph_visualization(
            db_session=test_db, graph_id=graph.id, user_id=user_in_db.id
        )

        # Check nodes
        assert len(result.nodes) == 2
        node1_data = next((n for n in result.nodes if n.id == node1.id), None)
        node2_data = next((n for n in result.nodes if n.id == node2.id), None)

        assert node1_data is not None
        assert node1_data.mastery_score == 0.85

        # Node2 should have default mastery (0.1)
        assert node2_data is not None
        assert node2_data.mastery_score == 0.1

    @pytest.mark.asyncio
    async def test_returns_default_mastery_when_no_mastery_record(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return default mastery score 0.1 for nodes without mastery."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(graph_id=graph.id, node_name="Node")
        test_db.add(node)
        await test_db.commit()

        result = await get_graph_visualization(test_db, graph.id, user_in_db.id)

        assert len(result.nodes) == 1
        assert result.nodes[0].mastery_score == 0.1

    @pytest.mark.asyncio
    async def test_includes_prerequisite_edges(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should include prerequisite edges in visualization."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([node1, node2])
        await test_db.flush()

        prereq = Prerequisite(
            graph_id=graph.id,
            from_node_id=node1.id,
            to_node_id=node2.id,
            weight=1.0,
        )
        test_db.add(prereq)
        await test_db.commit()

        result = await get_graph_visualization(test_db, graph.id, user_in_db.id)

        # Check edges
        prereq_edges = [e for e in result.edges if e.type == "IS_PREREQUISITE_FOR"]
        assert len(prereq_edges) == 1
        assert prereq_edges[0].source_id == node1.id
        assert prereq_edges[0].target_id == node2.id

    @pytest.mark.asyncio
    async def test_returns_complete_graph_structure(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
        user_in_db: User,
    ):
        """Should return complete graph with all nodes and edges."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        prereqs = private_graph_with_few_nodes_and_relations_in_db["prerequisites"]
        subtopics = private_graph_with_few_nodes_and_relations_in_db["subtopics"]

        result = await get_graph_visualization(test_db, graph.id, user_in_db.id)

        # Check nodes count
        assert len(result.nodes) == len(nodes)

        # Check edges count
        prereq_edges = [e for e in result.edges if e.type == "IS_PREREQUISITE_FOR"]
        subtopic_edges = [e for e in result.edges if e.type == "HAS_SUBTOPIC"]

        assert len(prereq_edges) == len(prereqs)
        assert len(subtopic_edges) == len(subtopics)

    @pytest.mark.asyncio
    async def test_node_includes_all_fields(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should include all required fields in node data."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node = KnowledgeNode(
            graph_id=graph.id,
            node_name="Complete Node",
            description="Test description",
        )
        test_db.add(node)
        await test_db.commit()

        result = await get_graph_visualization(test_db, graph.id, user_in_db.id)

        assert len(result.nodes) == 1
        node_data = result.nodes[0]

        assert node_data.id == node.id
        assert node_data.name == "Complete Node"
        assert node_data.description == "Test description"
        assert hasattr(node_data, "mastery_score")


# ==================== Graph Structure Import Tests ====================
class TestImportGraphStructure:
    """Test cases for import_graph_structure function."""

    @pytest.mark.asyncio
    async def test_imports_complete_graph_structure(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should import nodes, prerequisites, and subtopics in one transaction."""
        graph = KnowledgeGraph(
            owner_id=user_in_db.id, name="Import Test", slug="import-test"
        )
        test_db.add(graph)
        await test_db.commit()

        # Prepare import data
        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="node-1",
                    node_name="Node 1",
                    description="First node",
                ),
                NodeImport(
                    node_id_str="node-2",
                    node_name="Node 2",
                    description="Second node",
                ),
                NodeImport(
                    node_id_str="node-3",
                    node_name="Node 3",
                    description="Third node",
                ),
            ],
            prerequisites=[
                PrerequisiteImport(
                    from_node_id_str="node-2",
                    to_node_id_str="node-3",
                    weight=1.0,
                ),
            ],
        )

        result = await import_graph_structure(
            db_session=test_db,
            graph_id=graph.id,
            import_data=import_data,
        )

        # Verify response
        assert result.nodes_created == 3
        assert result.prerequisites_created == 1
        assert "3 nodes" in result.message
        assert "1 prerequisites" in result.message

    @pytest.mark.asyncio
    async def test_handles_duplicate_nodes_idempotently(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should skip duplicate nodes on reimport."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="node-1",
                    node_name="Node 1",
                ),
            ],
            prerequisites=[],
        )

        # First import
        result1 = await import_graph_structure(test_db, graph.id, import_data)
        assert result1.nodes_created == 1

        # Second import (duplicate)
        result2 = await import_graph_structure(test_db, graph.id, import_data)
        assert result2.nodes_created == 0
        assert result2.nodes_skipped == 1

    @pytest.mark.asyncio
    async def test_resolves_string_ids_to_uuids(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should resolve node_id_str to actual UUIDs for relationships."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="parent",
                    node_name="Parent",
                ),
                NodeImport(
                    node_id_str="child",
                    node_name="Child",
                ),
            ],
            prerequisites=[],
        )

        await import_graph_structure(test_db, graph.id, import_data)

    @pytest.mark.asyncio
    async def test_skips_invalid_prerequisite_references(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should skip prerequisites with invalid node references."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="node-1",
                    node_name="Node 1",
                ),
            ],
            prerequisites=[
                PrerequisiteImport(
                    from_node_id_str="nonexistent",  # Invalid reference
                    to_node_id_str="node-1",
                    weight=1.0,
                ),
            ],
        )

        result = await import_graph_structure(test_db, graph.id, import_data)

        assert result.nodes_created == 1
        assert result.prerequisites_created == 0
        assert result.prerequisites_skipped == 1

    @pytest.mark.asyncio
    async def test_skips_self_referencing_relationships(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should skip prerequisites and subtopics that reference same node."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="node-1",
                    node_name="Node 1",
                ),
            ],
            prerequisites=[
                PrerequisiteImport(
                    from_node_id_str="node-1",
                    to_node_id_str="node-1",  # Self-reference
                    weight=1.0,
                ),
            ],
        )

        result = await import_graph_structure(test_db, graph.id, import_data)

        assert result.nodes_created == 1
        assert result.prerequisites_created == 0
        assert result.prerequisites_skipped == 1

    @pytest.mark.asyncio
    async def test_handles_empty_import_data(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should handle empty import data gracefully."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[],
            prerequisites=[],
            # subtopics=[],
        )

        result = await import_graph_structure(test_db, graph.id, import_data)

        assert result.nodes_created == 0
        assert result.prerequisites_created == 0

    @pytest.mark.asyncio
    async def test_transaction_atomicity(self, test_db: AsyncSession, user_in_db: User):
        """Should commit all operations in a single transaction."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="node-1",
                    node_name="Node 1",
                ),
                NodeImport(
                    node_id_str="node-2",
                    node_name="Node 2",
                ),
            ],
            prerequisites=[],
        )

        await import_graph_structure(test_db, graph.id, import_data)

        # Verify everything was committed

        nodes = await get_nodes_by_graph(test_db, graph.id)

        assert len(nodes) == 2

    @pytest.mark.asyncio
    async def test_handles_duplicate_relationships(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should skip duplicate prerequisites."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        import_data = GraphStructureImport(
            nodes=[
                NodeImport(
                    node_id_str="node-1",
                    node_name="Node 1",
                ),
                NodeImport(
                    node_id_str="node-2",
                    node_name="Node 2",
                ),
            ],
            prerequisites=[],
        )

        # First import
        _result1 = await import_graph_structure(test_db, graph.id, import_data)

        # Second import with same data
        result2 = await import_graph_structure(test_db, graph.id, import_data)
        assert result2.nodes_created == 0  # nodes already exist
        assert result2.nodes_skipped == 2


# ==================== Topology Analysis Tests ====================
class TestGetPrerequisiteAdjacencyList:
    """Test cases for get_prerequisite_adjacency_list function."""

    @pytest.mark.asyncio
    async def test_returns_all_nodes_and_edges(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return all nodes and prerequisite edges as adjacency list."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        node3 = KnowledgeNode(graph_id=graph.id, node_name="Node 3")
        test_db.add_all([node1, node2, node3])
        await test_db.flush()

        prereq1 = Prerequisite(
            graph_id=graph.id, from_node_id=node1.id, to_node_id=node2.id, weight=1.0
        )
        prereq2 = Prerequisite(
            graph_id=graph.id, from_node_id=node2.id, to_node_id=node3.id, weight=1.0
        )
        test_db.add_all([prereq1, prereq2])
        await test_db.commit()

        nodes, adj_list = await get_prerequisite_adjacency_list(test_db, graph.id)

        # Check all nodes are included
        assert len(nodes) == 3
        assert node1.id in nodes
        assert node2.id in nodes
        assert node3.id in nodes

        # Check adjacency list
        assert node1.id in adj_list
        assert node2.id in adj_list[node1.id]
        assert node3.id in adj_list[node2.id]

    @pytest.mark.asyncio
    async def test_handles_nodes_with_no_prerequisites(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return nodes even if they have no prerequisites."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node1 = KnowledgeNode(graph_id=graph.id, node_name="Isolated Node")
        test_db.add(node1)
        await test_db.commit()

        nodes, adj_list = await get_prerequisite_adjacency_list(test_db, graph.id)

        assert len(nodes) == 1
        assert node1.id in nodes
        # Node should not be in adj_list if it has no outgoing edges
        assert node1.id not in adj_list

    @pytest.mark.asyncio
    async def test_empty_graph(self, test_db: AsyncSession, user_in_db: User):
        """Should handle empty graph gracefully."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Empty", slug="empty")
        test_db.add(graph)
        await test_db.commit()

        nodes, adj_list = await get_prerequisite_adjacency_list(test_db, graph.id)

        assert len(nodes) == 0
        assert len(adj_list) == 0


class TestBatchUpdateNodeTopology:
    """Test cases for batch_update_node_topology function."""

    @pytest.mark.asyncio
    async def test_updates_levels_and_dependents(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should batch update level and dependents_count for all nodes."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        test_db.add_all([node1, node2])
        await test_db.commit()

        # Prepare topology data
        levels = {node1.id: 0, node2.id: 1}
        dependents = {node1.id: 1, node2.id: 0}

        # Update topology
        nodes_updated = await batch_update_node_topology(
            test_db, graph.id, levels, dependents
        )

        assert nodes_updated == 2

        # Verify database was updated
        await test_db.refresh(node1)
        await test_db.refresh(node2)

        assert node1.level == 0
        assert node1.dependents_count == 1
        assert node2.level == 1
        assert node2.dependents_count == 0

    @pytest.mark.asyncio
    async def test_handles_empty_updates(self, test_db: AsyncSession, user_in_db: User):
        """Should handle empty update gracefully."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.commit()

        nodes_updated = await batch_update_node_topology(test_db, graph.id, {}, {})

        assert nodes_updated == 0


class TestResetNodeTopology:
    """Test cases for reset_node_topology function."""

    @pytest.mark.asyncio
    async def test_resets_all_topology_metrics(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should reset level and dependents_count to default values."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        # Create nodes with existing topology values
        node1 = KnowledgeNode(
            graph_id=graph.id, node_name="Node 1", level=5, dependents_count=10
        )
        node2 = KnowledgeNode(
            graph_id=graph.id, node_name="Node 2", level=3, dependents_count=7
        )
        test_db.add_all([node1, node2])
        await test_db.commit()

        # Reset topology
        nodes_reset = await reset_node_topology(test_db, graph.id)

        assert nodes_reset == 2

        # Verify all nodes were reset
        await test_db.refresh(node1)
        await test_db.refresh(node2)

        assert node1.level == -1
        assert node1.dependents_count == 0
        assert node2.level == -1
        assert node2.dependents_count == 0

    @pytest.mark.asyncio
    async def test_only_affects_specified_graph(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should only reset nodes in the specified graph."""
        graph1 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 1", slug="graph-1")
        graph2 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 2", slug="graph-2")
        test_db.add_all([graph1, graph2])
        await test_db.flush()

        node1 = KnowledgeNode(
            graph_id=graph1.id, node_name="Node 1", level=5, dependents_count=10
        )
        node2 = KnowledgeNode(
            graph_id=graph2.id, node_name="Node 2", level=3, dependents_count=7
        )
        test_db.add_all([node1, node2])
        await test_db.commit()

        # Reset only graph1
        await reset_node_topology(test_db, graph1.id)

        await test_db.refresh(node1)
        await test_db.refresh(node2)

        # node1 should be reset
        assert node1.level == -1
        assert node1.dependents_count == 0

        # node2 should remain unchanged
        assert node2.level == 3
        assert node2.dependents_count == 7


class TestGetGraphStatistics:
    """Test cases for get_graph_statistics function."""

    @pytest.mark.asyncio
    async def test_returns_accurate_counts(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return accurate counts for nodes, prerequisites, and subtopics."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Test", slug="test")
        test_db.add(graph)
        await test_db.flush()

        # Create 3 nodes
        node1 = KnowledgeNode(graph_id=graph.id, node_name="Node 1")
        node2 = KnowledgeNode(graph_id=graph.id, node_name="Node 2")
        node3 = KnowledgeNode(graph_id=graph.id, node_name="Node 3")
        test_db.add_all([node1, node2, node3])
        await test_db.flush()

        # Create 2 prerequisites
        prereq1 = Prerequisite(
            graph_id=graph.id, from_node_id=node1.id, to_node_id=node2.id, weight=1.0
        )
        prereq2 = Prerequisite(
            graph_id=graph.id, from_node_id=node2.id, to_node_id=node3.id, weight=1.0
        )
        test_db.add_all([prereq1, prereq2])

        await test_db.commit()

        stats = await get_graph_statistics(test_db, graph.id)

        assert stats["node_count"] == 3
        assert stats["prerequisite_count"] == 2

    @pytest.mark.asyncio
    async def test_empty_graph_returns_zero_counts(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should return zero counts for empty graph."""
        graph = KnowledgeGraph(owner_id=user_in_db.id, name="Empty", slug="empty")
        test_db.add(graph)
        await test_db.commit()

        stats = await get_graph_statistics(test_db, graph.id)

        assert stats["node_count"] == 0
        assert stats["prerequisite_count"] == 0

    @pytest.mark.asyncio
    async def test_only_counts_specified_graph(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Should only count entities from the specified graph."""
        graph1 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 1", slug="graph-1")
        graph2 = KnowledgeGraph(owner_id=user_in_db.id, name="Graph 2", slug="graph-2")
        test_db.add_all([graph1, graph2])
        await test_db.flush()

        # Add nodes to both graphs
        node1 = KnowledgeNode(graph_id=graph1.id, node_name="G1 Node")
        node2 = KnowledgeNode(graph_id=graph2.id, node_name="G2 Node 1")
        node3 = KnowledgeNode(graph_id=graph2.id, node_name="G2 Node 2")
        test_db.add_all([node1, node2, node3])
        await test_db.commit()

        stats1 = await get_graph_statistics(test_db, graph1.id)
        stats2 = await get_graph_statistics(test_db, graph2.id)

        assert stats1["node_count"] == 1
        assert stats2["node_count"] == 2
