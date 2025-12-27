"""
Tests for mastery CRUD operations.

These tests verify the core mastery database operations including:
- Basic CRUD: get_mastery, create_mastery, get_or_create_mastery
- Batch queries: get_masteries_by_user_and_graph, get_masteries_by_nodes
- Complex graph traversal: get_all_affected_parent_ids, get_prerequisite_roots_to_bonus
- Bulk operations: get_all_subtopics_for_parents_bulk
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.mastery import (
    create_mastery,
    get_all_affected_parent_ids,
    get_all_subtopics_for_parents_bulk,
    get_masteries_by_nodes,
    get_masteries_by_user_and_graph,
    get_mastery,
    get_or_create_mastery,
    get_prerequisite_roots_to_bonus,
)
from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.models.user import User, UserMastery


class TestGetMastery:
    """Test cases for get_mastery function."""

    @pytest.mark.asyncio
    async def test_returns_mastery_when_exists(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return the mastery record when it exists."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["calculus-basics"]

        # Create a mastery record
        mastery = UserMastery(
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
            cached_retrievability=0.9,
            last_updated=datetime.now(UTC),
        )
        test_db.add(mastery)
        await test_db.commit()
        await test_db.refresh(mastery)

        # Test retrieval
        result = await get_mastery(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
        )

        assert result is not None
        assert result.user_id == mastery.user_id
        assert result.graph_id == mastery.graph_id
        assert result.node_id == mastery.node_id
        assert result.cached_retrievability == 0.9

    @pytest.mark.asyncio
    async def test_returns_none_when_not_exists(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return None when mastery record doesn't exist."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["calculus-basics"]

        result = await get_mastery(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_nonexistent_uuids(
        self,
        test_db: AsyncSession,
    ):
        """Should return None when user/graph/node IDs don't exist."""
        result = await get_mastery(
            db_session=test_db,
            user_id=uuid4(),
            graph_id=uuid4(),
            node_id=uuid4(),
        )

        assert result is None


class TestCreateMastery:
    """Test cases for create_mastery function."""

    @pytest.mark.asyncio
    async def test_creates_mastery_successfully(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should create a new mastery record with correct attributes."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["derivatives"]

        mastery = await create_mastery(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
            cached_retrievability=0.85,
        )

        assert mastery is not None
        assert mastery.user_id == user_in_db.id
        assert mastery.graph_id == graph.id
        assert mastery.node_id == node.id
        assert mastery.cached_retrievability == 0.85
        assert mastery.last_updated is not None

    @pytest.mark.asyncio
    async def test_mastery_not_committed_automatically(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should add mastery to session but NOT commit (caller's responsibility)."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["integrals"]

        user_id = user_in_db.id
        graph_id = graph.id
        node_id = node.id

        mastery = await create_mastery(
            db_session=test_db,
            user_id=user_id,
            graph_id=graph_id,
            node_id=node_id,
            cached_retrievability=0.75,
        )

        # After rollback, it should not be persisted
        await test_db.rollback()

        # Verify it doesn't exist in database
        result = await get_mastery(
            db_session=test_db,
            user_id=user_id,
            graph_id=graph_id,
            node_id=node_id,
        )
        assert result is None


class TestGetOrCreateMastery:
    """Test cases for get_or_create_mastery function."""

    @pytest.mark.asyncio
    async def test_gets_existing_mastery_without_creating_new(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return existing mastery and was_created=False."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["chain-rule"]

        # Create initial mastery
        initial_mastery = UserMastery(
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
            cached_retrievability=0.6,
            last_updated=datetime.now(UTC),
        )
        test_db.add(initial_mastery)
        await test_db.commit()
        await test_db.refresh(initial_mastery)

        # Try to get_or_create
        mastery, was_created = await get_or_create_mastery(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
            cached_retrievability=0.95,  # This should be ignored
        )

        assert was_created is False
        assert mastery.user_id == initial_mastery.user_id
        assert mastery.graph_id == initial_mastery.graph_id
        assert mastery.node_id == initial_mastery.node_id
        assert mastery.cached_retrievability == 0.6  # Original value unchanged

    @pytest.mark.asyncio
    async def test_creates_new_mastery_when_not_exists(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should create new mastery and return was_created=True."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]
        node = nodes["integration-by-parts"]

        mastery, was_created = await get_or_create_mastery(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=node.id,
            cached_retrievability=0.5,
        )

        assert was_created is True
        assert mastery.user_id == user_in_db.id
        assert mastery.graph_id == graph.id
        assert mastery.node_id == node.id
        assert mastery.cached_retrievability == 0.5


class TestGetMasteriesByUserAndGraph:
    """Test cases for get_masteries_by_user_and_graph function."""

    @pytest.mark.asyncio
    async def test_returns_all_masteries_for_user_in_graph(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return all mastery records for a user in a specific graph."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # Create multiple mastery records
        mastery_records = []
        for key in ["calculus-basics", "derivatives", "integrals"]:
            mastery = UserMastery(
                user_id=user_in_db.id,
                graph_id=graph.id,
                node_id=nodes[key].id,
                cached_retrievability=0.8,
                last_updated=datetime.now(UTC),
            )
            test_db.add(mastery)
            mastery_records.append(mastery)

        await test_db.commit()

        # Retrieve all masteries
        result = await get_masteries_by_user_and_graph(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
        )

        assert len(result) == 3
        result_node_ids = {m.node_id for m in result}
        expected_node_ids = {nodes[key].id for key in ["calculus-basics", "derivatives", "integrals"]}
        assert result_node_ids == expected_node_ids

    @pytest.mark.asyncio
    async def test_returns_empty_list_when_no_masteries(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return empty list when user has no mastery in the graph."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]

        result = await get_masteries_by_user_and_graph(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
        )

        assert result == []


class TestGetMasteriesByNodes:
    """Test cases for get_masteries_by_nodes function."""

    @pytest.mark.asyncio
    async def test_returns_dict_mapping_node_ids_to_masteries(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return a dictionary mapping node_id -> UserMastery."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # Create mastery records
        node_keys = ["calculus-basics", "derivatives"]
        for key in node_keys:
            mastery = UserMastery(
                user_id=user_in_db.id,
                graph_id=graph.id,
                node_id=nodes[key].id,
                cached_retrievability=0.7,
                last_updated=datetime.now(UTC),
            )
            test_db.add(mastery)

        await test_db.commit()

        # Query masteries
        node_ids = [nodes[key].id for key in node_keys]
        result = await get_masteries_by_nodes(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_ids=node_ids,
        )

        assert len(result) == 2
        assert nodes["calculus-basics"].id in result
        assert nodes["derivatives"].id in result
        assert result[nodes["calculus-basics"].id].cached_retrievability == 0.7

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_empty_node_list(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return empty dict when node_ids list is empty."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]

        result = await get_masteries_by_nodes(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_ids=[],
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_only_returns_masteries_that_exist(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should only include nodes with existing mastery records."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # Create mastery for only one node
        mastery = UserMastery(
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_id=nodes["integrals"].id,
            cached_retrievability=0.65,
            last_updated=datetime.now(UTC),
        )
        test_db.add(mastery)
        await test_db.commit()

        # Query for multiple nodes, but only one has mastery
        node_ids = [nodes["integrals"].id, nodes["chain-rule"].id]
        result = await get_masteries_by_nodes(
            db_session=test_db,
            user_id=user_in_db.id,
            graph_id=graph.id,
            node_ids=node_ids,
        )

        assert len(result) == 1
        assert nodes["integrals"].id in result
        assert nodes["chain-rule"].id not in result


class TestGetAllAffectedParentIds:
    """Test cases for get_all_affected_parent_ids function (recursive CTE)."""

    @pytest.mark.asyncio
    async def test_finds_direct_parents(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should find direct parent nodes via subtopic relationships.
        
        Graph structure:
        - Calculus Basics -> Derivatives (parent)
        - Derivatives -> Chain Rule (parent)
        
        Starting from Chain Rule should find Derivatives at level 1.
        """
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # Start from "chain-rule" node
        result = await get_all_affected_parent_ids(
            db_session=test_db,
            graph_id=graph.id,
            start_node_ids=[nodes["chain-rule"].id],
        )

        # Should find "derivatives" as direct parent
        result_dict = {node_id: level for node_id, level in result}
        assert nodes["derivatives"].id in result_dict
        assert result_dict[nodes["derivatives"].id] == 1

    @pytest.mark.asyncio
    async def test_finds_multi_level_ancestors(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should find grandparents and higher ancestors.
        
        Graph structure:
        - Calculus Basics -> Derivatives -> Chain Rule
        
        Starting from Chain Rule should find:
        - Derivatives (level 1)
        - Calculus Basics (level 2)
        """
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        result = await get_all_affected_parent_ids(
            db_session=test_db,
            graph_id=graph.id,
            start_node_ids=[nodes["chain-rule"].id],
        )

        result_dict = {node_id: level for node_id, level in result}
        
        # Check all ancestors are found
        assert nodes["derivatives"].id in result_dict
        assert nodes["calculus-basics"].id in result_dict
        
        # Check levels are correct
        assert result_dict[nodes["derivatives"].id] == 1
        assert result_dict[nodes["calculus-basics"].id] == 2

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_empty_start_nodes(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return empty list when start_node_ids is empty."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]

        result = await get_all_affected_parent_ids(
            db_session=test_db,
            graph_id=graph.id,
            start_node_ids=[],
        )

        assert result == []

    @pytest.mark.asyncio
    async def test_handles_multiple_start_nodes(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should find all parents when starting from multiple nodes."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # Start from both "chain-rule" and "integration-by-parts"
        result = await get_all_affected_parent_ids(
            db_session=test_db,
            graph_id=graph.id,
            start_node_ids=[nodes["chain-rule"].id, nodes["integration-by-parts"].id],
        )

        result_dict = {node_id: level for node_id, level in result}

        # Should find both branches of parents
        assert nodes["derivatives"].id in result_dict
        assert nodes["integrals"].id in result_dict
        assert nodes["calculus-basics"].id in result_dict


class TestGetPrerequisiteRootsToBonus:
    """Test cases for get_prerequisite_roots_to_bonus function (recursive CTE)."""

    @pytest.mark.asyncio
    async def test_finds_direct_prerequisites(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should find direct prerequisites with depth 1.
        
        Graph structure:
        - Derivatives --[PREREQUISITE]--> Integrals
        
        Starting from Integrals should find Derivatives at depth 1.
        """
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        result = await get_prerequisite_roots_to_bonus(
            db_session=test_db,
            graph_id=graph.id,
            start_node_id=nodes["integrals"].id,
        )

        assert nodes["derivatives"].id in result
        assert result[nodes["derivatives"].id] == 1

    @pytest.mark.asyncio
    async def test_finds_multi_level_prerequisites(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should find prerequisites of prerequisites.
        
        Graph structure:
        - Chain Rule --[PREREQUISITE]--> Integration by Parts
        
        Even though this is just one level, we test the recursive capability.
        """
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        result = await get_prerequisite_roots_to_bonus(
            db_session=test_db,
            graph_id=graph.id,
            start_node_id=nodes["integration-by-parts"].id,
        )

        assert nodes["chain-rule"].id in result
        assert result[nodes["chain-rule"].id] == 1

    @pytest.mark.asyncio
    async def test_returns_empty_dict_when_no_prerequisites(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return empty dict when node has no prerequisites."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # "calculus-basics" has no prerequisites
        result = await get_prerequisite_roots_to_bonus(
            db_session=test_db,
            graph_id=graph.id,
            start_node_id=nodes["calculus-basics"].id,
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_minimum_depth_for_prerequisites(
        self,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Should return minimum depth when a prerequisite appears at multiple depths.
        
        This tests a more complex scenario where a node might be reachable
        through multiple prerequisite paths.
        """
        from app.models.knowledge_graph import KnowledgeGraph
        from app.models.knowledge_node import KnowledgeNode, Prerequisite

        # Create a custom graph for this test
        graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Complex Prerequisite Graph",
            slug="complex-prereq",
        )
        test_db.add(graph)
        await test_db.flush()

        # Create nodes: A, B, C, D
        node_a = KnowledgeNode(graph_id=graph.id, node_name="A")
        node_b = KnowledgeNode(graph_id=graph.id, node_name="B")
        node_c = KnowledgeNode(graph_id=graph.id, node_name="C")
        node_d = KnowledgeNode(graph_id=graph.id, node_name="D")
        
        test_db.add_all([node_a, node_b, node_c, node_d])
        await test_db.flush()

        # Create prerequisite chain:
        # A -> C (depth 1)
        # A -> B -> C (depth 1 -> 2)
        # So A should be returned with minimum depth 1
        prereq1 = Prerequisite(graph_id=graph.id, from_node_id=node_a.id, to_node_id=node_c.id)
        prereq2 = Prerequisite(graph_id=graph.id, from_node_id=node_a.id, to_node_id=node_b.id)
        prereq3 = Prerequisite(graph_id=graph.id, from_node_id=node_b.id, to_node_id=node_c.id)
        
        test_db.add_all([prereq1, prereq2, prereq3])
        await test_db.commit()

        # Query from node C
        result = await get_prerequisite_roots_to_bonus(
            db_session=test_db,
            graph_id=graph.id,
            start_node_id=node_c.id,
        )

        # Node A appears at depth 1 (direct) and depth 2 (via B)
        # Should return minimum depth = 1
        assert node_a.id in result
        assert result[node_a.id] == 1
        
        # Node B only appears at depth 1
        assert node_b.id in result
        assert result[node_b.id] == 1


class TestGetAllSubtopicsForParentsBulk:
    """Test cases for get_all_subtopics_for_parents_bulk function."""

    @pytest.mark.asyncio
    async def test_returns_subtopics_for_multiple_parents(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return subtopics grouped by parent_id."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        parent_ids = [nodes["calculus-basics"].id, nodes["derivatives"].id]
        
        result = await get_all_subtopics_for_parents_bulk(
            db_session=test_db,
            graph_id=graph.id,
            parent_node_ids=parent_ids,
        )

        # Calculus Basics has 2 subtopics: Derivatives and Integrals
        assert len(result[nodes["calculus-basics"].id]) == 2
        child_ids = [child_id for child_id, weight in result[nodes["calculus-basics"].id]]
        assert nodes["derivatives"].id in child_ids
        assert nodes["integrals"].id in child_ids

        # Derivatives has 1 subtopic: Chain Rule
        assert len(result[nodes["derivatives"].id]) == 1
        assert result[nodes["derivatives"].id][0][0] == nodes["chain-rule"].id

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_empty_parent_list(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return empty dict when parent_node_ids is empty."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]

        result = await get_all_subtopics_for_parents_bulk(
            db_session=test_db,
            graph_id=graph.id,
            parent_node_ids=[],
        )

        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_parent_with_no_subtopics(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should return empty list for parents that have no subtopics."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        # Chain Rule has no subtopics (it's a leaf node)
        result = await get_all_subtopics_for_parents_bulk(
            db_session=test_db,
            graph_id=graph.id,
            parent_node_ids=[nodes["chain-rule"].id],
        )

        assert nodes["chain-rule"].id in result
        assert result[nodes["chain-rule"].id] == []

    @pytest.mark.asyncio
    async def test_includes_subtopic_weights(
        self,
        test_db: AsyncSession,
        private_graph_with_few_nodes_and_relations_in_db: dict,
    ):
        """Should include weight information in the result tuples."""
        graph = private_graph_with_few_nodes_and_relations_in_db["graph"]
        nodes = private_graph_with_few_nodes_and_relations_in_db["nodes"]

        result = await get_all_subtopics_for_parents_bulk(
            db_session=test_db,
            graph_id=graph.id,
            parent_node_ids=[nodes["calculus-basics"].id],
        )

        # Each subtopic should be a tuple of (child_id, weight)
        subtopics = result[nodes["calculus-basics"].id]
        assert all(isinstance(item, tuple) and len(item) == 2 for item in subtopics)
        
        # Verify weights are floats
        for child_id, weight in subtopics:
            assert isinstance(weight, float)
            assert 0.0 <= weight <= 1.0
