import os
import tempfile
from unittest.mock import ANY, AsyncMock, patch

import pypdf
import pytest

from app.services.ai_services.pdf_extraction_service import PDFExtractionService
from app.utils.split_pdf import split_pdf


@pytest.fixture
def mock_pdf_service():
    # Mock settings to avoid API key error during init if not set
    with patch(
        "app.services.ai_services.pdf_extraction_service.settings"
    ) as mock_settings:
        mock_settings.GOOGLE_API_KEY = "fake_key"
        service = PDFExtractionService(api_key="fake_key")
        # Mock the actual Gemini call
        service._process_pdf_with_gemini = AsyncMock(return_value="Extracted Content")
        return service


@pytest.fixture
def big_pdf_file():
    """Creates a temporary PDF file with 5 blank pages."""
    fd, path = tempfile.mkstemp(suffix=".pdf")
    os.close(fd)

    writer = pypdf.PdfWriter()
    # Create a blank page
    writer.add_blank_page(width=72, height=72)
    # Duplicate it to make 5 pages
    for _ in range(4):
        writer.add_blank_page(width=72, height=72)

    with open(path, "wb") as f:
        writer.write(f)

    yield path

    if os.path.exists(path):
        os.remove(path)


@pytest.mark.asyncio
async def test_chunking_logic(mock_pdf_service, big_pdf_file):
    """Test that a 5-page PDF is split into 3 chunks if chunk_size=2."""

    chunk_size = 2

    # We expect 5 pages / 2 = 3 chunks (2, 2, 1 pages)

    result = await mock_pdf_service.extract_text_from_formatted_pdf(
        file_path=big_pdf_file, chunk_size=chunk_size
    )

    # Verify _process_pdf_with_gemini was called 3 times
    assert mock_pdf_service._process_pdf_with_gemini.call_count == 3

    # Verify result is joined
    expected_result = "Extracted Content\n\nExtracted Content\n\nExtracted Content"
    assert result == expected_result

    # Verify call args passed to gemini (should be paths to temp files)
    call_args_list = mock_pdf_service._process_pdf_with_gemini.call_args_list
    assert len(call_args_list) == 3

    # Check that temporary files were cleaned up?
    # The method cleans them up in finally.
    # We can check if the paths passed passed to the mock still exist?
    # They should NOT exist after the method returns.

    for args in call_args_list:
        path_arg = args[0][0]  # first arg of call
        # Mock calls happened, files were deleted after method return.
        # But we need to be sure test is running after method return. Yes, await returned.
        assert not os.path.exists(path_arg), f"Temp file {path_arg} was not cleaned up"


@pytest.mark.asyncio
async def test_no_chunking_needed(mock_pdf_service, big_pdf_file):
    """Test that a 5-page PDF is NOT split if chunk_size=10."""

    chunk_size = 10

    await mock_pdf_service.extract_text_from_formatted_pdf(
        file_path=big_pdf_file, chunk_size=chunk_size
    )

    # Verify _process_pdf_with_gemini was called 1 time
    assert mock_pdf_service._process_pdf_with_gemini.call_count == 1

    # Verify it was called with original file
    mock_pdf_service._process_pdf_with_gemini.assert_called_with(
        big_pdf_file, ANY, ANY  # prompt  # model
    )

    # Verify original file still exists
    assert os.path.exists(big_pdf_file)


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
