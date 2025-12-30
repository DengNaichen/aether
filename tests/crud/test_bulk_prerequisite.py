import pytest

from app.crud import prerequisite


@pytest.mark.asyncio
async def test_bulk_create_prerequisites_success(
    test_db, private_graph_with_few_nodes_and_relations_in_db
):
    """Test successful bulk creation of prerequisites."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    nodes = graph_data["nodes"]

    # Create new prerequisite relationships
    new_prerequisites = [
        (nodes["calculus-basics"].id, nodes["derivatives"].id, 0.9),  # Parent -> Child
        (
            nodes["integrals"].id,
            nodes["integration-by-parts"].id,
            0.7,
        ),  # Existing subtopic relationship
    ]

    result = await prerequisite.bulk_create_prerequisites(
        test_db, graph.id, new_prerequisites
    )

    assert result["count"] == 2
    assert "created" in result["message"].lower()

    # Verify they were created in the database
    all_prereqs = await prerequisite.get_prerequisites_by_graph(test_db, graph.id)
    assert len(all_prereqs) == 4


@pytest.mark.asyncio
async def test_bulk_create_prerequisites_skip_duplicates(
    test_db, private_graph_with_few_nodes_and_relations_in_db
):
    """Test that duplicate prerequisites are automatically skipped."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    # nodes = graph_data["nodes"]
    existing_prereqs = graph_data["prerequisites"]

    # Try to create duplicate of existing prerequisite
    duplicate_data = [
        (existing_prereqs[0].from_node_id, existing_prereqs[0].to_node_id, 0.95)
    ]

    result = await prerequisite.bulk_create_prerequisites(
        test_db, graph.id, duplicate_data
    )

    # Should skip the duplicate
    assert result["count"] == 0
    assert "processed 1" in result["message"].lower()

    # Verify no new prerequisites were added
    all_prereqs = await prerequisite.get_prerequisites_by_graph(test_db, graph.id)
    assert len(all_prereqs) == 2  # Still only the original 2


@pytest.mark.asyncio
async def test_bulk_create_prerequisites_empty_list(test_db, private_graph_in_db):
    """Test that empty list returns gracefully."""
    result = await prerequisite.bulk_create_prerequisites(
        test_db, private_graph_in_db.id, []
    )

    assert result["count"] == 0
    assert "no prerequisites" in result["message"].lower()


@pytest.mark.asyncio
async def test_bulk_create_prerequisites_mixed_valid_and_duplicate(
    test_db, private_graph_with_few_nodes_and_relations_in_db
):
    """Test bulk insert with mix of new and duplicate prerequisites."""
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    nodes = graph_data["nodes"]
    existing_prereqs = graph_data["prerequisites"]

    # Mix of duplicate and new
    mixed_data = [
        # Duplicate (should be skipped)
        (existing_prereqs[0].from_node_id, existing_prereqs[0].to_node_id, 0.95),
        # New (should be created)
        (nodes["calculus-basics"].id, nodes["chain-rule"].id, 0.8),
        # Another new (should be created)
        (nodes["calculus-basics"].id, nodes["integrals"].id, 0.6),
    ]

    result = await prerequisite.bulk_create_prerequisites(test_db, graph.id, mixed_data)

    # Should only create the 2 new ones
    assert result["count"] == 2
    assert "processed 3" in result["message"].lower()

    # Verify final count
    all_prereqs = await prerequisite.get_prerequisites_by_graph(test_db, graph.id)
    assert len(all_prereqs) == 4  # 2 original + 2 new


@pytest.mark.asyncio
async def test_bulk_create_prerequisites_ignores_leaf_validation(
    test_db, private_graph_with_few_nodes_and_relations_in_db
):
    """
    Test that bulk_create_prerequisites does NOT enforce leaf node validation.

    This is intentional for AI-generated graphs where leaf status is unknown.
    """
    graph_data = private_graph_with_few_nodes_and_relations_in_db
    graph = graph_data["graph"]
    nodes = graph_data["nodes"]

    # Create prerequisite pointing TO a parent node (non-leaf)
    # calculus-basics is a parent node (has subtopics), not a leaf
    non_leaf_prereq = [(nodes["derivatives"].id, nodes["calculus-basics"].id, 1.0)]

    # This should succeed (no leaf validation)
    result = await prerequisite.bulk_create_prerequisites(
        test_db, graph.id, non_leaf_prereq
    )

    assert result["count"] == 1

    # Verify it was created
    all_prereqs = await prerequisite.get_prerequisites_by_graph(test_db, graph.id)
    created_prereq = [
        p
        for p in all_prereqs
        if p.from_node_id == nodes["derivatives"].id
        and p.to_node_id == nodes["calculus-basics"].id
    ]
    assert len(created_prereq) == 1
    assert created_prereq[0].weight == 1.0
