"""Unit tests for PDF metadata extraction.

Tests the get_pdf_metadata() function.
"""

import os
import tempfile

import pypdf
import pytest

from app.utils.pdf_metadata import get_pdf_metadata


class TestGetPDFMetadata:
    """Test cases for get_pdf_metadata() function."""

    @pytest.fixture
    def sample_pdf(self):
        """Create a temporary PDF with specific metadata."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_blank_page(width=612, height=792)

        # Add metadata
        writer.add_metadata({"/Title": "Test Document", "/Author": "Test Author"})

        with open(path, "wb") as f:
            writer.write(f)

        yield path

        if os.path.exists(path):
            os.remove(path)

    def test_get_metadata_success(self, sample_pdf):
        """Should correctly extract metadata from a valid PDF."""
        metadata = get_pdf_metadata(sample_pdf)

        assert metadata["page_count"] == 2
        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "Test Author"
        assert metadata["file_size"] > 0

    def test_get_metadata_file_not_found(self):
        """Should raise FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            get_pdf_metadata("/path/to/non_existent.pdf")

    def test_get_metadata_invalid_pdf(self):
        """Should raise ValueError for invalid PDF file."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            with open(path, "w") as f:
                f.write("Not a PDF")

            with pytest.raises(ValueError, match="Invalid or corrupted PDF file"):
                get_pdf_metadata(path)
        finally:
            if os.path.exists(path):
                os.remove(path)
