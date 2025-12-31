import logging
from collections.abc import Callable

from app.schemas.file_pipeline import FilePipelineStatus

logger = logging.getLogger(__name__)


class PDFPipeline:
    """
    Orchestrates the lifecycle of a PDF processing task.
    Focuses on 'Pre-OCR' stages: validation, metadata extraction, and preparation.
    """

    def __init__(self, task_id: int, file_path: str):
        self.task_id = task_id
        self.file_path = file_path
        self.stages: list[Callable] = []
        self.intermediate_files: list[str] = []  # Track files to cleanup
        self.context = {
            "task_id": task_id,
            "file_path": file_path,
            "status": FilePipelineStatus.PENDING,
            "metadata": {},
            "intermediate_files": self.intermediate_files,
        }

    def add_stage(self, func: Callable):
        self.stages.append(func)

    async def execute(self, cleanup: bool = True):
        """
        Executes the registered stages in order.
        If cleanup is True, removes all associated files after completion or failure.
        """
        logger.info(f"Starting pipeline for task {self.task_id}")
        self.context["status"] = FilePipelineStatus.IN_PROGRESS

        try:
            for stage in self.stages:
                logger.info(f"Executing stage: {stage.__name__}")
                await stage(self.context)

            self.context["status"] = FilePipelineStatus.COMPLETED
            return self.context
        except Exception as e:
            logger.error(f"Pipeline failed at task {self.task_id}: {e}")
            self.context["status"] = FilePipelineStatus.FAILED
            self.context["error"] = str(e)
            raise e
        finally:
            if cleanup:
                self._cleanup()

    def _cleanup(self):
        """Internal cleanup logic for task-related files."""
        import os

        from app.utils.storage import cleanup_task_storage

        logger.info(f"Running cleanup for task {self.task_id}...")

        # 1. Clean up the task directory (best practice: centralized cleanup)
        cleanup_task_storage(self.task_id)

        # 2. Clean up any other specific files registered outside the task dir
        for f in self.intermediate_files:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


# --- Pre-OCR Stage Implementation ---


async def validate_and_extract_metadata_stage(context: dict):
    """
    Stage: Validates file existence and extracts metadata.
    Uses the utility function from preprocess_files.
    """
    from app.utils.pdf_metadata import get_pdf_metadata

    file_path = context.get("file_path")
    # This utility handles existence check and pypdf reading
    metadata = get_pdf_metadata(file_path)

    # Update context with the retrieved metadata
    context["metadata"].update(metadata)
    logger.info(
        f"Metadata extracted for task {context['task_id']}: {metadata['page_count']} pages"
    )


async def check_page_limit_stage(context: dict):
    """
    Stage: Ensures the PDF doesn't exceed a specific page limit (e.g., for cost control).
    """
    MAX_PAGES = 100  # Configurable limit
    page_count = context["metadata"].get("page_count", 0)

    if page_count > MAX_PAGES:
        raise ValueError(
            f"PDF too large: {page_count} pages (Max allowed: {MAX_PAGES})"
        )


async def validate_file_type_stage(context: dict):
    """
    Stage: Ensures the file is a PDF based on its extension.
    """
    file_path = context.get("file_path")
    if not file_path or not file_path.lower().endswith(".pdf"):
        raise ValueError("Invalid file format. Only PDF files are supported.")


async def detect_handwriting_stage(context: dict):
    """
    Stage: Detects if the PDF is likely handwritten or scanned.
    Updates context['metadata']['is_handwritten'].
    """
    from app.utils.is_handwritten import is_handwritten

    file_path = context.get("file_path")
    # Heuristic analysis to determine if the PDF is handwritten
    handwritten = is_handwritten(file_path)

    context["metadata"]["is_handwritten"] = handwritten
    logger.info(f"Handwriting detection for task {context['task_id']}: {handwritten}")


async def extract_text_stage(context: dict):
    """
    Stage: Extracts text content from the PDF using Gemini.
    Selects the extraction method based on the 'is_handwritten' metadata.
    """
    from app.services.ai_services.pdf_extraction import PDFExtractionService

    extractor = PDFExtractionService()
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


async def save_markdown_stage(context: dict):
    """
    Stage: Saves the extracted markdown content to a persistent location.
    Useful for holding data before committing to the database.
    """
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


async def generate_graph_stage(context: dict):
    """
    Stage 2: Generate knowledge graph from markdown content and save to database.

    Prerequisites:
    - context["markdown_content"] must exist
    - context["graph_id"] must exist
    - context["db_session"] must exist

    Outputs:
    - context["graph_stats"]: Graph generation statistics
        {
            "nodes_created": int,
            "prerequisites_created": int,
            "subtopics_created": int,
            "total_nodes": int,
            "max_level": int
        }

    Raises:
        ValueError: If required context fields are missing or AI generation fails
    """
    from app.services.graph_generation_service import GraphGenerationService

    # Validate required context
    graph_id = context.get("graph_id")
    markdown_content = context.get("markdown_content")
    db_session = context.get("db_session")

    if not markdown_content:
        raise ValueError("markdown_content is required in context for graph generation")
    if not graph_id:
        raise ValueError("graph_id is required in context for graph generation")
    if not db_session:
        raise ValueError("db_session is required in context for graph generation")

    # Optional: user guidance for AI
    user_guidance = context.get("user_guidance", "")
    incremental = context.get("incremental", True)  # Default to incremental mode

    logger.info(
        f"Starting graph generation for graph_id={graph_id}, "
        f"incremental={incremental}, content_length={len(markdown_content)}"
    )

    try:
        # Create service and generate graph
        service = GraphGenerationService(db_session)
        stats = await service.create_graph_from_markdown(
            graph_id=graph_id,
            markdown_content=markdown_content,
            user_guidance=user_guidance,
            incremental=incremental,
        )

        # Store stats in context
        context["graph_stats"] = stats

        logger.info(
            f"Graph generation completed: {stats['nodes_created']} nodes created, "
            f"{stats['total_nodes']} total nodes, max_level={stats['max_level']}"
        )

    except Exception as e:
        logger.error(f"Graph generation failed: {e}", exc_info=True)
        context["graph_generation_error"] = str(e)
        raise
