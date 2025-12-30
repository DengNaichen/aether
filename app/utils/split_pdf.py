import os
import tempfile

import pypdf

from app.utils.pdf_metadata import logger


def split_pdf(file_path: str, chunk_size: int) -> list[str]:
    """Splits a PDF into chunks. Returns paths to temporary files (or original if small).

    Args:
        file_path: Absolute path to the source PDF.
        chunk_size: Number of pages per chunk.

    Returns:
        List of file paths. If valid splitting occurs, these are temporary files
        that must be cleaned up by the caller.
    """
    try:
        reader = pypdf.PdfReader(file_path)
        total_pages = len(reader.pages)

        # If file is small enough, no need to split
        if total_pages <= chunk_size:
            return [file_path]

        logger.info(
            f"Splitting PDF ({total_pages} pages) into chunks of {chunk_size}..."
        )
        chunk_paths = []

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

            chunk_paths.append(tmp_path)

        return chunk_paths

    except Exception as e:
        logger.error(f"Failed to split PDF: {e}")
        raise
