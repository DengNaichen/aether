"""
Unit tests for NodeGenerationService.

Phase 1 (Current): Node-only generation from markdown
    - Creating nodes from markdown
    - Entity resolution + embedding generation
    - Error handling
"""

from unittest.mock import AsyncMock, patch

import pytest

from app.schemas.knowledge_node import (
    KnowledgeNodeLLM,
    KnowledgeNodesLLM,
    KnowledgeNodeWithEmbedding,
)
from app.services.ai.entity_resolution import EntityResolutionResult
from app.services.pipeline.node_generation_pipeline import NodeGenerationService


@pytest.mark.asyncio
async def test_create_node_from_markdown_persists_nodes(test_db, private_graph_in_db):
    """Test creating nodes from markdown with persistence."""
    service = NodeGenerationService(test_db)

    extracted = KnowledgeNodesLLM(
        nodes=[
            KnowledgeNodeLLM(name="AI Node 1", description="From AI"),
            KnowledgeNodeLLM(name="AI Node 2", description="From AI"),
        ]
    )
    resolved = EntityResolutionResult(
        new_nodes=[
            KnowledgeNodeWithEmbedding(
                name="AI Node 1", description="From AI", embedding=[0.1, 0.2]
            ),
            KnowledgeNodeWithEmbedding(
                name="AI Node 2", description="From AI", embedding=[0.3, 0.4]
            ),
        ],
        duplicates_found=0,
    )

    with (
        patch(
            "app.services.pipeline.node_generation_pipeline.generate_nodes_from_markdown",
            return_value=extracted,
        ) as mock_generate,
        patch(
            "app.services.pipeline.node_generation_pipeline.EntityResolutionService"
        ) as mock_resolver_cls,
        patch.object(
            NodeGenerationService, "_persist_nodes", new_callable=AsyncMock
        ) as mock_persist,
        patch(
            "app.services.pipeline.node_generation_pipeline.knowledge_node.get_nodes_by_graph",
            new_callable=AsyncMock,
        ) as mock_get_nodes,
    ):
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.resolve_entities = AsyncMock(return_value=resolved)
        mock_persist.return_value = 2
        mock_get_nodes.return_value = [object(), object()]

        result = await service.create_node_from_markdown(
            graph_id=private_graph_in_db.id,
            markdown_content="# Test Content\nSome markdown here",
            incremental=False,
        )

    assert result["nodes_created"] == 2
    assert result["total_nodes"] == 2
    mock_generate.assert_called_once()
    mock_persist.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_node_from_markdown_empty_result(test_db, private_graph_in_db):
    """Test empty extraction returns zero counts."""
    service = NodeGenerationService(test_db)
    extracted = KnowledgeNodesLLM(nodes=[])
    resolved = EntityResolutionResult(new_nodes=[], duplicates_found=0)

    with (
        patch(
            "app.services.pipeline.node_generation_pipeline.generate_nodes_from_markdown",
            return_value=extracted,
        ),
        patch(
            "app.services.pipeline.node_generation_pipeline.EntityResolutionService"
        ) as mock_resolver_cls,
        patch.object(
            NodeGenerationService, "_persist_nodes", new_callable=AsyncMock
        ) as mock_persist,
        patch(
            "app.services.pipeline.node_generation_pipeline.knowledge_node.get_nodes_by_graph",
            new_callable=AsyncMock,
        ) as mock_get_nodes,
    ):
        mock_resolver = mock_resolver_cls.return_value
        mock_resolver.resolve_entities = AsyncMock(return_value=resolved)
        mock_persist.return_value = 0
        mock_get_nodes.return_value = []

        result = await service.create_node_from_markdown(
            graph_id=private_graph_in_db.id,
            markdown_content="# Empty Content",
            incremental=False,
        )

    assert result["nodes_created"] == 0
    assert result["total_nodes"] == 0


@pytest.mark.asyncio
async def test_create_node_from_markdown_propagates_ai_error(
    test_db, private_graph_in_db
):
    """Test that AI extraction errors are propagated."""
    service = NodeGenerationService(test_db)

    with patch(
        "app.services.pipeline.node_generation_pipeline.generate_nodes_from_markdown",
        side_effect=ValueError("AI failure"),
    ):
        with pytest.raises(ValueError, match="AI failure"):
            await service.create_node_from_markdown(
                graph_id=private_graph_in_db.id,
                markdown_content="# Test Content",
            )
