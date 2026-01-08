import logging
import os
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager

import pypdf

logger = logging.getLogger(__name__)


@contextmanager
def split_pdf(file_path: str, chunk_size: int) -> Iterator[list[str]]:
    """Context manager that splits a PDF into chunks and auto-cleans temporary files.

    This function splits large PDFs into smaller chunks for processing. It returns
    a context manager that yields the list of chunk file paths and automatically
    cleans up any temporary files when the context exits.

    Args:
        file_path: Absolute path to the source PDF.
        chunk_size: Number of pages per chunk.

    Yields:
        List of file paths. If no splitting occurred (PDF is small enough),
        returns a list containing only the original file path. Otherwise,
        returns paths to temporary chunk files.

    Example:
        with split_pdf("large.pdf", chunk_size=10) as chunks:
            for chunk_path in chunks:
                process(chunk_path)
        # Temporary files automatically cleaned up here

    Raises:
        Exception: If PDF reading or splitting fails.
    """
    chunks = []
    try:
        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)

        # If file is small enough, no need to split
        if total_pages <= chunk_size:
            chunks = [file_path]
            yield chunks
            return

        logger.info(
            f"Splitting PDF ({total_pages} pages) into chunks of {chunk_size}..."
        )

        for start_page in range(0, total_pages, chunk_size):
            end_page = min(start_page + chunk_size, total_pages)
            writer = pypdf.PdfWriter()

            for i in range(start_page, end_page):
                writer.add_page(reader.pages[i])

            # Create temp file
            fd, tmp_path = tempfile.mkstemp(
                suffix=f"_chunk_{start_page}-{end_page}.pdf"
            )
            os.close(fd)  # Close file descriptor immediately, we only need path

            with open(tmp_path, "wb") as f:
                writer.write(f)

            chunks.append(tmp_path)

        yield chunks

    except Exception as e:
        logger.error(f"Failed to split PDF: {e}")
        raise

    finally:
        # Clean up temporary chunk files (not the original)
        for path in chunks:
            if path != file_path and os.path.exists(path):
                try:
                    os.remove(path)
                    logger.debug(f"Cleaned up temp chunk: {path}")
                except Exception as cleanup_err:
                    logger.warning(f"Failed to delete temp file {path}: {cleanup_err}")
