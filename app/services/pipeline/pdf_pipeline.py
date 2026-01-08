"""
PDF Pipeline - Orchestration layer for PDF extraction.

This module provides a high-level pipeline for processing PDF files,
coordinating validation, metadata extraction, handwriting detection,
text extraction (via PDFExtractionService), and markdown storage.
"""

import logging

from app.schemas.file_pipeline import FilePipelineStatus
from app.services.ai.pdf_extraction import PDFExtractionService
from app.utils.pdf_metadata import get_pdf_metadata
from app.utils.storage import cleanup_task_storage

logger = logging.getLogger(__name__)


class PDFPipeline:
    """High-level pipeline for PDF extraction with validation and storage."""

    def __init__(self, extractor: PDFExtractionService | None = None):
        """Initialize the pipeline with an optional extractor instance."""
        self._extractor = extractor

    @property
    def extractor(self) -> PDFExtractionService:
        """Lazy-initialize the extractor to avoid API key issues at import time."""
        if self._extractor is None:
            self._extractor = PDFExtractionService()
        return self._extractor

    async def run(
        self,
        file_path: str,
        *,
        task_id: str | None = None,
        graph_id: str | None = None,
        enforce_page_limit: bool = True,
        save_markdown: bool = False,
        cleanup: bool = False,
    ) -> dict:
        """Run the PDF extraction pipeline and return the context.

        Args:
            file_path: Path to the PDF file.
            task_id: Optional task identifier for tracking.
            graph_id: Optional graph ID for storage organization.
            enforce_page_limit: Whether to enforce page count limits.
            save_markdown: Whether to save extracted markdown to storage.
            cleanup: Whether to cleanup task storage after completion.

        Returns:
            Context dict with status, metadata, and extracted content.
        """
        resolved_task_id = task_id or "pdf_extraction"
        context = {
            "task_id": resolved_task_id,
            "file_path": file_path,
            "status": FilePipelineStatus.IN_PROGRESS,
            "metadata": {},
            "intermediate_files": [],
        }
        if graph_id:
            context["graph_id"] = graph_id

        try:
            await _validate_file_type(context)
            await _validate_and_extract_metadata(context)
            if enforce_page_limit:
                await _check_page_limit(context)
            await _detect_handwriting(context)
            await _extract_text(context, self.extractor)
            if save_markdown:
                await _save_markdown(context)

            context["status"] = FilePipelineStatus.COMPLETED
            return context
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            context["status"] = FilePipelineStatus.FAILED
            context["error"] = str(e)
            raise
        finally:
            if cleanup and task_id:
                cleanup_task_storage(task_id)


# --- Pipeline Stages ---


async def _validate_file_type(context: dict):
    """Stage: Ensures the file is a PDF based on its extension."""
    file_path = context.get("file_path")
    if not file_path or not file_path.lower().endswith(".pdf"):
        raise ValueError("Invalid file format. Only PDF files are supported.")


async def _validate_and_extract_metadata(context: dict):
    """Stage: Validates file existence and extracts metadata."""
    file_path = context.get("file_path")
    metadata = get_pdf_metadata(file_path)

    context["metadata"].update(metadata)
    logger.info(
        f"Metadata extracted for task {context['task_id']}: {metadata['page_count']} pages"
    )


async def _check_page_limit(context: dict):
    """Stage: Ensures the PDF doesn't exceed a specific page limit."""
    MAX_PAGES = 100  # Configurable limit
    page_count = context["metadata"].get("page_count", 0)

    if page_count > MAX_PAGES:
        raise ValueError(
            f"PDF too large: {page_count} pages (Max allowed: {MAX_PAGES})"
        )


async def _detect_handwriting(context: dict):
    """Stage: Detects if the PDF is likely handwritten or scanned."""
    from app.utils.is_handwritten import is_handwritten

    file_path = context.get("file_path")
    handwritten = is_handwritten(file_path)

    context["metadata"]["is_handwritten"] = handwritten
    logger.info(f"Handwriting detection for task {context['task_id']}: {handwritten}")


async def _extract_text(context: dict, extractor: PDFExtractionService):
    """Stage: Extracts text content from the PDF using Gemini."""
    file_path = context.get("file_path")
    is_handwritten = context["metadata"].get("is_handwritten", False)

    if is_handwritten:
        logger.info(f"Task {context['task_id']}: Using handwriting extraction path.")
        content = await extractor.extract_handwritten_notes(file_path)
    else:
        logger.info(f"Task {context['task_id']}: Using formatted PDF extraction path.")
        content = await extractor.extract_text_from_formatted_pdf(file_path)

    context["markdown_content"] = content
    logger.info(
        f"Task {context['task_id']}: Text extraction completed. Length: {len(content)} chars."
    )


async def _save_markdown(context: dict):
    """Stage: Saves the extracted markdown content to a persistent location."""
    from app.utils.storage import save_graph_markdown, save_task_markdown

    task_id = context.get("task_id")
    graph_id = context.get("graph_id")
    content = context.get("markdown_content")

    if content:
        if graph_id:
            file_path = save_graph_markdown(graph_id, content)
        else:
            file_path = save_task_markdown(task_id, content)

        context["metadata"]["markdown_file_path"] = file_path
        logger.info(f"Task {task_id}: Markdown saved to {file_path}")
    else:
        logger.warning(f"Task {task_id}: No markdown content found to save.")
