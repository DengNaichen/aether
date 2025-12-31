from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.pdf_pipeline import generate_graph_stage, save_markdown_stage


@pytest.mark.asyncio
async def test_save_markdown_stage_uses_graph_markdown():
    context = {
        "task_id": "task-1",
        "graph_id": "graph-1",
        "markdown_content": "# Content",
        "metadata": {},
    }

    with (
        patch(
            "app.utils.storage.save_graph_markdown",
            return_value="/tmp/graph.md",
        ) as mock_save_graph,
        patch("app.utils.storage.save_task_markdown") as mock_save_task,
    ):
        await save_markdown_stage(context)

    mock_save_graph.assert_called_once_with("graph-1", "# Content")
    mock_save_task.assert_not_called()
    assert context["metadata"]["markdown_file_path"] == "/tmp/graph.md"


@pytest.mark.asyncio
async def test_generate_graph_stage_calls_service_with_incremental():
    db_session = MagicMock()
    context = {
        "graph_id": "graph-1",
        "markdown_content": "# Content",
        "db_session": db_session,
        "user_guidance": "Keep concise",
        "incremental": True,
    }
    stats = {
        "nodes_created": 1,
        "prerequisites_created": 0,
        "total_nodes": 1,
        "max_level": 0,
    }

    with patch(
        "app.services.graph_generation_service.GraphGenerationService"
    ) as mock_service:
        mock_instance = mock_service.return_value
        mock_instance.create_graph_from_markdown = AsyncMock(return_value=stats)

        await generate_graph_stage(context)

    mock_service.assert_called_once_with(db_session)
    mock_instance.create_graph_from_markdown.assert_awaited_once_with(
        graph_id="graph-1",
        markdown_content="# Content",
        user_guidance="Keep concise",
        incremental=True,
    )
    assert context["graph_stats"] == stats
