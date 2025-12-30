import logging
import os

import pypdf

logger = logging.getLogger(__name__)


def get_pdf_metadata(file_path: str) -> dict:
    """Extracts metadata from a PDF file.

    Args:
        file_path: Absolute path to the PDF.

    Returns:
        A dictionary containing page_count, title, author, and file_size.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    try:
        reader = pypdf.PdfReader(file_path)
        info = reader.metadata
        return {
            "page_count": len(reader.pages),
            "file_size": os.path.getsize(file_path),
            "title": info.get("/Title") if info else None,
            "author": info.get("/Author") if info else None,
        }
    except Exception as e:
        logger.error(f"Failed to extract PDF metadata: {e}")
        raise ValueError(f"Invalid or corrupted PDF file: {e}") from e
