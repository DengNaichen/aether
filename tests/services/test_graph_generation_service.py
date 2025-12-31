"""
Unit tests for GraphGenerationService.

Phase 1 (Current): New graph generation from markdown
    - Creating graphs from markdown (incremental=False)
    - Basic persistence of nodes and relationships
    - Topology computation
    - Error handling

Phase 2 (Future - RAG): Incremental updates with intelligent merging
    - Loading existing graphs (_load_existing_graph)
    - Graph merging with entity resolution (merge_graphs)
    - Incremental updates (incremental=True)
    - Deduplication and conflict resolution
"""


from unittest.mock import patch

import pytest

from app.schemas.knowledge_node import (
    GraphStructureLLM,
    KnowledgeNodeLLM,
    RelationshipLLM,
)
from app.services.graph_generation_service import GraphGenerationService

# ============================================================================
# Phase 2 Tests (Future - RAG): Incremental Updates
# ============================================================================
# These tests are for future implementation when we add:
# - RAG-based graph retrieval and merging
# - Entity resolution and deduplication
# - Incremental updates to existing graphs
# ============================================================================

# @pytest.mark.asyncio
# async def test_load_existing_graph_empty(test_db, private_graph_in_db):
#     """Test loading existing graph when graph has no nodes."""
#     service = GraphGenerationService(test_db)
#
#     result = await service._load_existing_graph(private_graph_in_db.id)
#
#     assert isinstance(result, GraphStructureLLM)
#     assert len(result.nodes) == 0
#     assert len(result.relationships) == 0
#
#
# @pytest.mark.asyncio
# async def test_load_existing_graph_with_data(
#     test_db, private_graph_with_few_nodes_and_relations_in_db
# ):
#     """Test loading existing graph with nodes and relationships."""
#     graph_data = private_graph_with_few_nodes_and_relations_in_db
#     graph = graph_data["graph"]
#
#     service = GraphGenerationService(test_db)
#     result = await service._load_existing_graph(graph.id)
#
#     # Should have 5 nodes
#     assert len(result.nodes) == 5
#     node_names = {node.name for node in result.nodes}
#     assert "Calculus Basics" in node_names
#     assert "Derivatives" in node_names
#
#     # Should have 2 prerequisites (subtopics removed)
#     assert len(result.relationships) == 2
#
#     # Check prerequisite relationships
#     prereq_rels = [r for r in result.relationships if r.label == "IS_PREREQUISITE_FOR"]
#     assert len(prereq_rels) == 2


# ============================================================================
# Phase 1 Tests (Current): Basic Graph Persistence
# ============================================================================

@pytest.mark.asyncio
async def test_persist_graph_new_nodes(test_db, private_graph_in_db):
    """Test persisting a graph with only new nodes."""
    service = GraphGenerationService(test_db)

    # Create a simple LLM graph
    llm_graph = GraphStructureLLM(
        nodes=[
            KnowledgeNodeLLM(name="Node A", description="Description A"),
            KnowledgeNodeLLM(name="Node B", description="Description B"),
        ],
        relationships=[],
    )

    result = await service._persist_graph(private_graph_in_db.id, llm_graph)

    assert result["nodes_created"] == 2
    assert result["prerequisites_created"] == 0
    # assert result["subtopics_created"] == 0


@pytest.mark.asyncio
async def test_persist_graph_with_relationships(test_db, private_graph_in_db):
    """Test persisting a graph with nodes and relationships."""
    service = GraphGenerationService(test_db)

    # Create LLM graph with relationships
    llm_graph = GraphStructureLLM(
        nodes=[
            KnowledgeNodeLLM(name="Node A", description="Description A"),
            KnowledgeNodeLLM(name="Node B", description="Description B"),
            KnowledgeNodeLLM(name="Node C", description="Description C"),
        ],
        relationships=[
            RelationshipLLM(
                label="IS_PREREQUISITE_FOR",
                source_name="Node A",
                target_name="Node B",
                weight=1.0,
            ),
            # RelationshipLLM(
            #     label="HAS_SUBTOPIC",
            #     parent_name="Node C",
            #     child_name="Node A",
            #     weight=0.5,
            # ),
        ],
    )

    result = await service._persist_graph(private_graph_in_db.id, llm_graph)

    assert result["nodes_created"] == 3
    assert result["prerequisites_created"] == 1
    # assert result["subtopics_created"] == 1


# Phase 2 Test: Deduplication (Future - RAG)
# @pytest.mark.asyncio
# async def test_persist_graph_skips_duplicates(
#     test_db, private_graph_with_few_nodes_and_relations_in_db
# ):
#     """Test that persisting existing nodes skips duplicates."""
#     graph_data = private_graph_with_few_nodes_and_relations_in_db
#     graph = graph_data["graph"]
#
#     service = GraphGenerationService(test_db)
#
#     # Try to persist nodes that already exist
#     llm_graph = GraphStructureLLM(
#         nodes=[
#             KnowledgeNodeLLM(name="Derivatives", description="Updated description"),
#             KnowledgeNodeLLM(name="New Node", description="This is new"),
#         ],
#         relationships=[],
#     )
#
#     result = await service._persist_graph(graph.id, llm_graph)
#
#     # Should only create the new node
#     assert result["nodes_created"] == 1


@pytest.mark.asyncio
async def test_persist_graph_skips_invalid_relationships(test_db, private_graph_in_db):
    """Test that relationships referencing non-existent nodes are skipped."""
    service = GraphGenerationService(test_db)

    # Create graph with relationship pointing to non-existent node
    llm_graph = GraphStructureLLM(
        nodes=[
            KnowledgeNodeLLM(name="Node A", description="Description A"),
        ],
        relationships=[
            RelationshipLLM(
                label="IS_PREREQUISITE_FOR",
                source_name="Node A",
                target_name="Non-Existent Node",  # This doesn't exist
                weight=1.0,
            ),
        ],
    )

    result = await service._persist_graph(private_graph_in_db.id, llm_graph)

    assert result["nodes_created"] == 1
    assert result["prerequisites_created"] == 0  # Should be skipped


# ============================================================================
# Phase 1 Tests (Current): End-to-End Graph Generation
# ============================================================================


@pytest.mark.asyncio
@patch("app.services.graph_generation_service.process_markdown")
async def test_create_graph_from_markdown_non_incremental(
    mock_process_markdown, test_db, private_graph_in_db
):
    """Test creating graph from markdown in non-incremental mode (Phase 1)."""
    # Mock AI service response
    mock_graph = GraphStructureLLM(
        nodes=[
            KnowledgeNodeLLM(name="AI Node 1", description="From AI"),
            KnowledgeNodeLLM(name="AI Node 2", description="From AI"),
        ],
        relationships=[
            RelationshipLLM(
                label="IS_PREREQUISITE_FOR",
                source_name="AI Node 1",
                target_name="AI Node 2",
                weight=1.0,
            )
        ],
    )
    mock_process_markdown.return_value = mock_graph

    service = GraphGenerationService(test_db)

    result = await service.create_graph_from_markdown(
        graph_id=private_graph_in_db.id,
        markdown_content="# Test Content\nSome markdown here",
        incremental=False,
    )

    # Verify results
    assert result["nodes_created"] == 2
    assert result["prerequisites_created"] == 1
    assert result["total_nodes"] == 2
    assert "max_level" in result


# Phase 2 Tests: Incremental Updates (Future - RAG)
# @pytest.mark.asyncio
# @patch("app.services.ai_services.generate_graph.process_markdown")
# @patch("app.services.ai_services.generate_graph.merge_graphs")
# async def test_create_graph_from_markdown_incremental(
#     mock_merge_graphs,
#     mock_process_markdown,
#     test_db,
#     private_graph_with_few_nodes_and_relations_in_db,
# ):
#     """Test creating graph from markdown in incremental mode."""
#     graph_data = private_graph_with_few_nodes_and_relations_in_db
#     graph = graph_data["graph"]
#
#     # Mock AI service response (new content)
#     new_graph = GraphStructureLLM(
#         nodes=[
#             KnowledgeNodeLLM(name="AI Node New", description="New from AI"),
#         ],
#         relationships=[],
#     )
#     mock_process_markdown.return_value = new_graph
#
#     # Mock merge_graphs to return combined graph
#     merged_graph = GraphStructureLLM(
#         nodes=[
#             # Existing nodes + new node
#             KnowledgeNodeLLM(name="Derivatives", description="Existing"),
#             KnowledgeNodeLLM(name="AI Node New", description="New from AI"),
#         ],
#         relationships=[],
#     )
#     mock_merge_graphs.return_value = merged_graph
#
#     service = GraphGenerationService(test_db)
#
#     result = await service.create_graph_from_markdown(
#         graph_id=graph.id,
#         markdown_content="# New Content",
#         incremental=True,
#     )
#
#     # Verify merge_graphs was called with existing and new graphs
#     assert mock_merge_graphs.called
#     call_args = mock_merge_graphs.call_args[0][0]  # First positional argument
#     assert len(call_args) == 2  # [existing_graph, new_graph]
#
#     # Should only create the new node (existing should be skipped as duplicate)
#     assert result["nodes_created"] == 1
#     # Total should be original 5 + 1 new = 6
#     assert result["total_nodes"] == 6


@pytest.mark.asyncio
@patch("app.services.graph_generation_service.process_markdown")
async def test_create_graph_from_markdown_ai_failure(
    mock_process_markdown, test_db, private_graph_in_db
):
    """Test error handling when AI service fails."""
    # Mock AI service to return None (failure)
    mock_process_markdown.return_value = None

    service = GraphGenerationService(test_db)

    with pytest.raises(ValueError, match="AI service failed"):
        await service.create_graph_from_markdown(
            graph_id=private_graph_in_db.id,
            markdown_content="# Test Content",
        )
