import logging
import shutil
from pathlib import Path

from app.core.config import settings

logger = logging.getLogger(__name__)

# Base directory for all temporary storage related to the pipeline
STORAGE_BASE = Path(settings.PIPELINE_STORAGE_PATH)

# Directory for results that should persist until manually moved to DB
RESULTS_BASE = Path(settings.PIPELINE_RESULTS_PATH)


def get_task_storage_path(task_id: int) -> Path:
    """Returns the dedicated directory for a specific task."""
    path = STORAGE_BASE / f"task_{task_id}"
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_task_markdown(task_id: int, content: str) -> str:
    """
    Saves the extracted markdown to a persistent results directory.
    This stays after the pipeline cleanup until decided otherwise.
    """
    RESULTS_BASE.mkdir(parents=True, exist_ok=True)
    file_path = RESULTS_BASE / f"task_{task_id}_content.md"
    file_path.write_text(content, encoding="utf-8")
    logger.info(f"Saved extracted markdown for task {task_id} to {file_path}")
    return str(file_path)


def save_graph_markdown(graph_id: str, content: str) -> str:
    """
    Saves the extracted markdown to a graph-specific directory.
    Replaces existing content for the same graph if it exists (simplification).
    """
    import time

    graph_dir = RESULTS_BASE / f"graph_{graph_id}"
    graph_dir.mkdir(parents=True, exist_ok=True)

    # We use a timestamped filename to allow history, but returns the latest
    filename = f"extracted_{int(time.time())}.md"
    file_path = graph_dir / filename

    file_path.write_text(content, encoding="utf-8")
    logger.info(f"Saved extracted markdown for graph {graph_id} to {file_path}")
    return str(file_path)


def save_upload_file(task_id: int, original_filename: str, content: bytes) -> str:
    """
    Saves an uploaded file to a deterministic path based on task_id.
    Standardizes the filename to 'input.pdf' to simplify pipeline stages.
    """
    task_dir = get_task_storage_path(task_id)
    # We use a fixed name 'input.pdf' internally, but could also slugify the original name
    file_path = task_dir / "input.pdf"

    with open(file_path, "wb") as f:
        f.write(content)

    logger.info(f"Saved upload for task {task_id} to {file_path}")
    return str(file_path)


def cleanup_task_storage(task_id: int):
    """Removes all files associated with a task."""
    task_dir = STORAGE_BASE / f"task_{task_id}"
    if task_dir.exists() and task_dir.is_dir():
        try:
            shutil.rmtree(task_dir)
            logger.info(f"Cleaned up storage for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup task {task_id} storage: {e}")
