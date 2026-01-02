"""
Unit tests for EntityResolutionService.

Tests cover:
- Exact duplicate detection (similarity = 1.0)
- High similarity detection (similarity > threshold)
- Low similarity (distinct nodes)
- Empty graph scenarios
- No embeddings available
"""

from unittest.mock import patch

import pytest

from app.core.config import settings
from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.schemas.knowledge_node import KnowledgeNodeLLM
from app.services.ai_services.entity_resolution import EntityResolutionService


def _vec(val: float = 0.5) -> list[float]:
    """Helper to create a test embedding vector with variation."""
    import numpy as np
    # Create distinct vectors based on val
    # Use different patterns for different values to ensure low similarity
    if val < 0.5:
        # Low values: concentrate in first half
        vector = np.zeros(settings.GEMINI_EMBEDDING_DIM)
        vector[:settings.GEMINI_EMBEDDING_DIM//2] = val
    else:
        # High values: concentrate in second half
        vector = np.zeros(settings.GEMINI_EMBEDDING_DIM)
        vector[settings.GEMINI_EMBEDDING_DIM//2:] = val

    # Normalize to unit length
    norm = np.linalg.norm(vector)
    if norm > 0:
        vector = vector / norm
    return vector.tolist()


@pytest.mark.asyncio
async def test_resolve_entities_exact_duplicate(test_db, user_in_db):
    """Test detection of exact duplicates (similarity = 1.0)."""
    # Create graph with existing node
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Test Graph", slug="test", description="Test"
    )
    test_db.add(graph)
    await test_db.flush()

    existing_node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Newton's First Law",
        node_id_str="node_1",
        description="An object at rest stays at rest",
        content_embedding=_vec(0.8),
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    test_db.add(existing_node)
    await test_db.commit()

    # New node with identical content
    new_nodes = [
        KnowledgeNodeLLM(
            name="Newton's First Law",
            description="An object at rest stays at rest",
        )
    ]

    # Mock embedding service to return identical embedding
    service = EntityResolutionService(test_db)

    async def mock_embed_text(text: str):
        return _vec(0.8)  # Same as existing node

    with patch.object(service.embedding_service, '_embed_text', new=mock_embed_text):
        result = await service.resolve_entities(graph.id, new_nodes)

    # Should detect as duplicate
    assert result.duplicates_found == 1
    assert result.new_nodes_count == 0
    # Use the computed ID from the node
    node_id = new_nodes[0].id
    assert result.node_mapping[node_id] == existing_node.id
    assert result.similarity_scores[node_id] >= 0.99  # Very high similarity


@pytest.mark.asyncio
async def test_resolve_entities_high_similarity(test_db, user_in_db):
    """Test detection of semantically similar nodes (above threshold)."""
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Test Graph", slug="test", description="Test"
    )
    test_db.add(graph)
    await test_db.flush()

    existing_node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Newton's First Law",
        node_id_str="node_1",
        description="Law of inertia",
        content_embedding=_vec(0.8),
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    test_db.add(existing_node)
    await test_db.commit()

    # New node with similar but different name
    new_nodes = [
        KnowledgeNodeLLM(
            name="Law of Inertia",  # Different name, same concept
            description="Objects maintain their state of motion",
        )
    ]

    service = EntityResolutionService(test_db)

    # Mock to return similar but not identical embedding
    async def mock_embed_text(text: str):
        return _vec(0.82)  # Slightly different, but high cosine similarity

    with patch.object(service.embedding_service, '_embed_text', new=mock_embed_text):
        result = await service.resolve_entities(graph.id, new_nodes)

    # Should detect as duplicate (similarity will be high due to similar vectors)
    assert result.duplicates_found == 1
    assert result.new_nodes_count == 0
    node_id = new_nodes[0].id
    assert result.node_mapping[node_id] == existing_node.id


@pytest.mark.asyncio
async def test_resolve_entities_low_similarity(test_db, user_in_db):
    """Test that distinct nodes are not marked as duplicates."""
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Test Graph", slug="test", description="Test"
    )
    test_db.add(graph)
    await test_db.flush()

    existing_node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Velocity",
        node_id_str="node_1",
        description="Rate of change of position",
        content_embedding=_vec(0.2),
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    test_db.add(existing_node)
    await test_db.commit()

    # Completely different concept
    new_nodes = [
        KnowledgeNodeLLM(
            name="Photosynthesis",
            description="Process by which plants make food",
        )
    ]

    service = EntityResolutionService(test_db)

    # Mock to return very different embedding
    async def mock_embed_text(text: str):
        return _vec(0.9)  # Very different from 0.2

    with patch.object(service.embedding_service, '_embed_text', new=mock_embed_text):
        result = await service.resolve_entities(graph.id, new_nodes)

    # Should NOT detect as duplicate
    assert result.duplicates_found == 0
    assert result.new_nodes_count == 1
    node_id = new_nodes[0].id
    assert result.node_mapping[node_id] is None  # Truly new node


@pytest.mark.asyncio
async def test_resolve_entities_empty_graph(test_db, user_in_db):
    """Test resolution when graph has no existing nodes."""
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Empty Graph", slug="empty", description="Test"
    )
    test_db.add(graph)
    await test_db.commit()

    new_nodes = [
        KnowledgeNodeLLM(name="Node 1", description="First node"),
        KnowledgeNodeLLM(name="Node 2", description="Second node"),
    ]

    service = EntityResolutionService(test_db)
    result = await service.resolve_entities(graph.id, new_nodes)

    # All nodes should be new
    assert result.duplicates_found == 0
    assert result.new_nodes_count == 2
    assert result.node_mapping[new_nodes[0].id] is None
    assert result.node_mapping[new_nodes[1].id] is None


@pytest.mark.asyncio
async def test_resolve_entities_no_embeddings(test_db, user_in_db):
    """Test resolution when existing nodes have no embeddings."""
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Test Graph", slug="test", description="Test"
    )
    test_db.add(graph)
    await test_db.flush()

    # Node without embedding
    existing_node = KnowledgeNode(
        graph_id=graph.id,
        node_name="Node without embedding",
        node_id_str="node_1",
        description="No embedding",
        content_embedding=None,  # No embedding!
    )
    test_db.add(existing_node)
    await test_db.commit()

    new_nodes = [
        KnowledgeNodeLLM(name="New Node", description="Test"),
    ]

    service = EntityResolutionService(test_db)
    result = await service.resolve_entities(graph.id, new_nodes)

    # Should treat as all new (no embeddings to compare against)
    assert result.duplicates_found == 0
    assert result.new_nodes_count == 1
    node_id = new_nodes[0].id
    assert result.node_mapping[node_id] is None


@pytest.mark.asyncio
async def test_resolve_entities_multiple_candidates(test_db, user_in_db):
    """Test that highest similarity match is chosen when multiple candidates exist."""
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Test Graph", slug="test", description="Test"
    )
    test_db.add(graph)
    await test_db.flush()

    # Two existing nodes with different embeddings
    node_1 = KnowledgeNode(
        graph_id=graph.id,
        node_name="Similar Node 1",
        node_id_str="node_1",
        content_embedding=_vec(0.3),  # Low value (first half of vector)
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    node_2 = KnowledgeNode(
        graph_id=graph.id,
        node_name="Similar Node 2",
        node_id_str="node_2",
        content_embedding=_vec(0.9),  # High value (second half of vector)
        embedding_model=settings.GEMINI_EMBEDDING_MODEL,
    )
    test_db.add_all([node_1, node_2])
    await test_db.commit()

    new_nodes = [
        KnowledgeNodeLLM(name="Test Node", description="Test"),
    ]

    service = EntityResolutionService(test_db)

    # Mock to return embedding closer to node_2 (high value, second half)
    async def mock_embed_text(text: str):
        return _vec(0.85)  # Also high value, should match node_2

    with patch.object(service.embedding_service, '_embed_text', new=mock_embed_text):
        result = await service.resolve_entities(graph.id, new_nodes)

    # Should match to node_2 (higher similarity)
    assert result.duplicates_found == 1
    node_id = new_nodes[0].id
    assert result.node_mapping[node_id] == node_2.id


@pytest.mark.asyncio
async def test_resolve_entities_disabled(test_db, user_in_db):
    """Test that resolution is skipped when disabled in settings."""
    graph = KnowledgeGraph(
        owner_id=user_in_db.id, name="Test Graph", slug="test", description="Test"
    )
    test_db.add(graph)
    await test_db.commit()

    new_nodes = [
        KnowledgeNodeLLM(name="Node 1", description="Test"),
    ]

    # Temporarily disable entity resolution
    original_setting = settings.ENTITY_RESOLUTION_ENABLED
    settings.ENTITY_RESOLUTION_ENABLED = False

    try:
        service = EntityResolutionService(test_db)
        result = await service.resolve_entities(graph.id, new_nodes)

        # Should treat all as new without checking
        assert result.duplicates_found == 0
        assert result.new_nodes_count == 1
        node_id = new_nodes[0].id
        assert result.node_mapping[node_id] is None
    finally:
        settings.ENTITY_RESOLUTION_ENABLED = original_setting
