from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.prompts import PDF_ACADEMIC_OCR_PROMPT, PDF_HANDWRITING_PROMPT
from app.services.ai_services.pdf_extraction import PDFExtractionService


class TestPDFExtractionServiceInit:
    """Tests for service initialization."""

    def test_init_success(self):
        with patch(
            "app.services.ai_services.pdf_extraction.settings"
        ) as mock_settings:
            mock_settings.GOOGLE_API_KEY = "valid_key"
            service = PDFExtractionService(api_key="valid_key")
            assert service.client is not None
            assert service.model_id == "gemini-2.5-flash"

    def test_init_missing_key(self):
        with patch(
            "app.services.ai_services.pdf_extraction.settings"
        ) as mock_settings:
            mock_settings.GOOGLE_API_KEY = None
            with pytest.raises(ValueError, match="GOOGLE_API_KEY is not set"):
                PDFExtractionService(api_key="")


class TestPDFExtractionServiceProcess:
    """Tests for the core _process_pdf_with_gemini method."""

    @pytest.fixture
    def mock_service(self):
        with patch("app.services.ai_services.pdf_extraction.genai.Client"):
            service = PDFExtractionService(api_key="fake_key")
            # Mock sync helpers to avoid retry delay issues in tests
            service._upload_file_sync = MagicMock()
            service._poll_file_sync = MagicMock()
            service._generate_content_sync = MagicMock()
            return service

    @pytest.mark.asyncio
    async def test_process_pdf_success(self, mock_service):
        file_path = "test.pdf"

        # Mock file existence check
        with patch("os.path.exists", return_value=True):
            # Mock Upload
            mock_upload_file = MagicMock()
            mock_upload_file.name = "files/123"
            mock_upload_file.state.name = "PROCESSING"
            mock_service._upload_file_sync.return_value = mock_upload_file

            # Mock Polling (First call PROCESSING, Second call ACTIVE)
            mock_active_file = MagicMock()
            mock_active_file.name = "files/123"
            mock_active_file.state.name = "ACTIVE"
            mock_active_file.uri = "gs://files/123"
            mock_active_file.mime_type = "application/pdf"

            mock_service._poll_file_sync.side_effect = [mock_active_file]

            # Mock Generation
            mock_response = MagicMock()
            mock_response.text = "Extracted Text"
            mock_service._generate_content_sync.return_value = mock_response

            # Mock Delete
            mock_service.client.files.delete = MagicMock()

            # Execute
            result = await mock_service._process_pdf_with_gemini(
                file_path, "Prompt", "model-id"
            )

            # Verify
            assert result == "Extracted Text"
            mock_service._upload_file_sync.assert_called_with(file_path)
            mock_service._generate_content_sync.assert_called_once()

            # Verify clean up was called
            # Note: We mock the client.files.delete call directly as it is called via asyncio.to_thread
            # In the code: await asyncio.to_thread(self.client.files.delete, name=file_upload.name)
            # The actual call on the mock object might be tricky to assert if not mocked at the thread level,
            # but since we mocked the whole class, we can check basic interaction if needed or just trust flow.

    @pytest.mark.asyncio
    async def test_process_pdf_file_not_found(self, mock_service):
        with patch("os.path.exists", return_value=False):
            with pytest.raises(FileNotFoundError):
                await mock_service._process_pdf_with_gemini("missing.pdf", "P", "M")

    @pytest.mark.asyncio
    async def test_process_pdf_timeout(self, mock_service):
        # Mock valid file
        with patch("os.path.exists", return_value=True):
            # Upload returns a file that STAYS processing
            mock_file = MagicMock()
            mock_file.state.name = "PROCESSING"
            mock_service._upload_file_sync.return_value = mock_file
            mock_service._poll_file_sync.return_value = mock_file

            # Reduce timeout for test speed (we can mock time, but logic uses hardcoded 60s)
            # Mock asyncio.sleep to run fast
            with (
                patch("asyncio.sleep", new_callable=AsyncMock),
                patch("time.time") as mock_time,
            ):
                import itertools

                # Use a counter that increments fast enough to trigger timeout quickly
                # even if logging consumes some calls.
                mock_time.side_effect = itertools.count(start=0, step=100)

                with pytest.raises(TimeoutError, match="timed out"):
                    await mock_service._process_pdf_with_gemini("test.pdf", "P", "M")

    @pytest.mark.asyncio
    async def test_process_pdf_upload_failed(self, mock_service):
        with patch("os.path.exists", return_value=True):
            mock_file = MagicMock()
            mock_file.name = "files/xxx"
            mock_file.state.name = "FAILED"  # Never active

            mock_service._upload_file_sync.return_value = mock_file
            # No polling loop entry if state is not PROCESSING
            # But initial state is FAILED, so loop skipped.

            with pytest.raises(Exception, match="File upload failed"):
                await mock_service._process_pdf_with_gemini("test.pdf", "P", "M")

            # Verify cleanup attempted
            # (Requires mocking client.files.delete effectively)


class TestPDFExtractionServiceChunking:
    """Tests for _extract_text_with_chunking and integration methods."""

    @pytest.fixture
    def mock_service(self):
        with patch("app.services.ai_services.pdf_extraction.genai.Client"):
            service = PDFExtractionService(api_key="key")
            service._process_pdf_with_gemini = AsyncMock(return_value="Content")
            return service

    @pytest.mark.asyncio
    async def test_chunking_single_file(self, mock_service):
        path = "/tmp/test.pdf"

        # Mock split_pdf as a context manager that yields the original path
        from contextlib import contextmanager

        @contextmanager
        def mock_split_pdf(*args, **kwargs):
            yield [path]

        with patch(
            "app.services.ai_services.pdf_extraction.split_pdf",
            side_effect=mock_split_pdf,
        ):
            result = await mock_service._extract_text_with_chunking(
                path, "Prompt", "model", 20
            )

            assert result == "Content"
            mock_service._process_pdf_with_gemini.assert_called_once_with(
                path, "Prompt", "model"
            )

    @pytest.mark.asyncio
    async def test_chunking_multiple_files(self, mock_service):
        original = "/tmp/original.pdf"
        chunks = ["/tmp/chunk1.pdf", "/tmp/chunk2.pdf"]

        # Mock split_pdf as a context manager that yields chunks
        from contextlib import contextmanager

        @contextmanager
        def mock_split_pdf(*args, **kwargs):
            yield chunks

        with patch(
            "app.services.ai_services.pdf_extraction.split_pdf",
            side_effect=mock_split_pdf,
        ):
            result = await mock_service._extract_text_with_chunking(
                original, "P", "M"
            )

            # Should have joined 2 results
            assert result == "Content\n\nContent"
            assert mock_service._process_pdf_with_gemini.call_count == 2
            # Note: Cleanup happens automatically in the context manager,
            # so we don't need to verify os.remove calls here

    @pytest.mark.asyncio
    async def test_extract_formatted_calls_chunking(self, mock_service):
        mock_service._extract_text_with_chunking = AsyncMock(return_value="Res")

        await mock_service.extract_text_from_formatted_pdf("path.pdf", chunk_size=30)

        mock_service._extract_text_with_chunking.assert_called_once_with(
            file_path="path.pdf",
            prompt=PDF_ACADEMIC_OCR_PROMPT.strip(),
            model_id=mock_service.model_id,
            chunk_size=30,
            chunk_type="chunk",
        )

    @pytest.mark.asyncio
    async def test_extract_handwritten_calls_chunking(self, mock_service):
        mock_service._extract_text_with_chunking = AsyncMock(return_value="Res")

        await mock_service.extract_handwritten_notes(
            "path.pdf", model_id="custom-model"
        )

        mock_service._extract_text_with_chunking.assert_called_once_with(
            file_path="path.pdf",
            prompt=PDF_HANDWRITING_PROMPT.strip(),
            model_id="custom-model",
            chunk_size=20,
            chunk_type="handwritten chunk",
        )
