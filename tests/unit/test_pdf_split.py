# import os
# import tempfile
# from unittest.mock import ANY, AsyncMock, patch

# import pypdf
# import pytest

# from app.services.ai_services.pdf_service import PDFExtractionService


# @pytest.fixture
# def mock_pdf_service():
#     # Mock settings to avoid API key error during init if not set
#     with patch("app.services.ai_services.pdf_service.settings") as mock_settings:
#         mock_settings.GOOGLE_API_KEY = "fake_key"
#         service = PDFExtractionService(api_key="fake_key")
#         # Mock the actual Gemini call
#         service._process_pdf_with_gemini = AsyncMock(return_value="Extracted Content")
#         return service


# @pytest.fixture
# def big_pdf_file():
#     """Creates a temporary PDF file with 5 blank pages."""
#     fd, path = tempfile.mkstemp(suffix=".pdf")
#     os.close(fd)

#     writer = pypdf.PdfWriter()
#     # Create a blank page
#     writer.add_blank_page(width=72, height=72)
#     # Duplicate it to make 5 pages
#     for _ in range(4):
#         writer.add_blank_page(width=72, height=72)

#     with open(path, "wb") as f:
#         writer.write(f)

#     yield path

#     if os.path.exists(path):
#         os.remove(path)


# @pytest.mark.asyncio
# async def test_chunking_logic(mock_pdf_service, big_pdf_file):
#     """Test that a 5-page PDF is split into 3 chunks if chunk_size=2."""

#     chunk_size = 2

#     # We expect 5 pages / 2 = 3 chunks (2, 2, 1 pages)

#     result = await mock_pdf_service.extract_text_from_formatted_pdf(
#         file_path=big_pdf_file, chunk_size=chunk_size
#     )

#     # Verify _process_pdf_with_gemini was called 3 times
#     assert mock_pdf_service._process_pdf_with_gemini.call_count == 3

#     # Verify result is joined
#     expected_result = "Extracted Content\n\nExtracted Content\n\nExtracted Content"
#     assert result == expected_result

#     # Verify call args passed to gemini (should be paths to temp files)
#     call_args_list = mock_pdf_service._process_pdf_with_gemini.call_args_list
#     assert len(call_args_list) == 3

#     # Check that temporary files were cleaned up?
#     # The method cleans them up in finally.
#     # We can check if the paths passed passed to the mock still exist?
#     # They should NOT exist after the method returns.

#     for args in call_args_list:
#         path_arg = args[0][0]  # first arg of call
#         # Mock calls happened, files were deleted after method return.
#         # But we need to be sure test is running after method return. Yes, await returned.
#         assert not os.path.exists(path_arg), f"Temp file {path_arg} was not cleaned up"


# @pytest.mark.asyncio
# async def test_no_chunking_needed(mock_pdf_service, big_pdf_file):
#     """Test that a 5-page PDF is NOT split if chunk_size=10."""

#     chunk_size = 10

#     await mock_pdf_service.extract_text_from_formatted_pdf(
#         file_path=big_pdf_file, chunk_size=chunk_size
#     )

#     # Verify _process_pdf_with_gemini was called 1 time
#     assert mock_pdf_service._process_pdf_with_gemini.call_count == 1

#     # Verify it was called with original file
#     mock_pdf_service._process_pdf_with_gemini.assert_called_with(
#         big_pdf_file, ANY, ANY  # prompt  # model
#     )

#     # Verify original file still exists
#     assert os.path.exists(big_pdf_file)
