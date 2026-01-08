from unittest.mock import AsyncMock, patch

import pytest

from app.services.pipeline.pdf_pipeline import _extract_text, _save_markdown


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
        await _save_markdown(context)

    mock_save_graph.assert_called_once_with("graph-1", "# Content")
    mock_save_task.assert_not_called()
    assert context["metadata"]["markdown_file_path"] == "/tmp/graph.md"


@pytest.mark.asyncio
async def test_extract_text_uses_handwriting_flag():
    extractor = AsyncMock()
    extractor.extract_text_from_formatted_pdf = AsyncMock(
        return_value="# Digital Content"
    )
    extractor.extract_handwritten_notes = AsyncMock(
        return_value="# Handwritten Content"
    )

    context = {
        "task_id": "task-1",
        "file_path": "/tmp/test.pdf",
        "metadata": {"is_handwritten": False},
    }

    await _extract_text(context, extractor)
    extractor.extract_text_from_formatted_pdf.assert_awaited_once_with(
        "/tmp/test.pdf"
    )
    assert context["markdown_content"] == "# Digital Content"

    context["metadata"]["is_handwritten"] = True
    await _extract_text(context, extractor)
    extractor.extract_handwritten_notes.assert_awaited_once_with("/tmp/test.pdf")
    assert context["markdown_content"] == "# Handwritten Content"
