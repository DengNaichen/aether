import os
import tempfile

import pypdf
import pytest

from app.utils.split_pdf import split_pdf


class TestSplitPDF:
    """Test cases for split_pdf() function."""

    @pytest.fixture
    def small_pdf(self):
        """Create a temporary PDF with 3 pages."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        writer = pypdf.PdfWriter()
        for _ in range(3):
            writer.add_blank_page(width=612, height=792)

        with open(path, "wb") as f:
            writer.write(f)

        yield path

        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture
    def large_pdf(self):
        """Create a temporary PDF with 10 pages."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        writer = pypdf.PdfWriter()
        for _ in range(10):
            writer.add_blank_page(width=612, height=792)

        with open(path, "wb") as f:
            writer.write(f)

        yield path

        if os.path.exists(path):
            os.remove(path)

    def test_small_pdf_no_splitting(self, small_pdf):
        """PDF with 3 pages and chunk_size=5 should return original path."""
        result = split_pdf(small_pdf, chunk_size=5)

        assert len(result) == 1
        assert result[0] == small_pdf
        # Original file should still exist
        assert os.path.exists(small_pdf)

    def test_large_pdf_splitting(self, large_pdf):
        """PDF with 10 pages and chunk_size=3 should create 4 chunks."""
        result = split_pdf(large_pdf, chunk_size=3)

        try:
            # Should create 4 chunks: [0-2], [3-5], [6-8], [9]
            assert len(result) == 4

            # Verify each chunk exists and has correct page count
            expected_page_counts = [3, 3, 3, 1]
            for i, chunk_path in enumerate(result):
                assert os.path.exists(chunk_path)
                assert chunk_path != large_pdf  # Should be temp files

                # Verify page count
                reader = pypdf.PdfReader(chunk_path)
                assert len(reader.pages) == expected_page_counts[i]

        finally:
            # Clean up temporary chunk files
            for chunk_path in result:
                if chunk_path != large_pdf and os.path.exists(chunk_path):
                    os.remove(chunk_path)

    def test_exact_chunk_size(self, large_pdf):
        """PDF with 10 pages and chunk_size=10 should return original."""
        result = split_pdf(large_pdf, chunk_size=10)

        assert len(result) == 1
        assert result[0] == large_pdf

    def test_single_page_pdf(self):
        """Single page PDF should return original path."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            writer = pypdf.PdfWriter()
            writer.add_blank_page(width=612, height=792)

            with open(path, "wb") as f:
                writer.write(f)

            result = split_pdf(path, chunk_size=5)

            assert len(result) == 1
            assert result[0] == path

        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_chunk_size_one(self, small_pdf):
        """chunk_size=1 should create one file per page."""
        result = split_pdf(small_pdf, chunk_size=1)

        try:
            assert len(result) == 3

            for chunk_path in result:
                assert os.path.exists(chunk_path)
                reader = pypdf.PdfReader(chunk_path)
                assert len(reader.pages) == 1

        finally:
            for chunk_path in result:
                if chunk_path != small_pdf and os.path.exists(chunk_path):
                    os.remove(chunk_path)

    def test_invalid_pdf_raises_exception(self):
        """Invalid PDF file should raise an exception."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)

        try:
            # Write invalid content
            with open(path, "w") as f:
                f.write("This is not a valid PDF")

            with pytest.raises(pypdf.errors.PdfReadError):
                split_pdf(path, chunk_size=5)

        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_temp_file_naming(self, large_pdf):
        """Verify temporary files have descriptive names."""
        result = split_pdf(large_pdf, chunk_size=3)

        try:
            # Check that chunk files have chunk info in name
            for chunk_path in result:
                if chunk_path != large_pdf:
                    assert "_chunk_" in chunk_path
                    assert chunk_path.endswith(".pdf")

        finally:
            for chunk_path in result:
                os.remove(chunk_path)
