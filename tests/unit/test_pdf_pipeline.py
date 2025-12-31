import os
import tempfile

import pypdf
import pytest

from app.schemas.file_pipeline import FilePipelineStatus
from app.services.pdf_pipeline import (
    PDFPipeline,
    check_page_limit_stage,
    detect_handwriting_stage,
    extract_text_stage,
    save_markdown_stage,
    validate_and_extract_metadata_stage,
    validate_file_type_stage,
)
from app.utils.storage import save_upload_file


class TestPDFPipeline:
    """Tests for the PDFPipeline orchestration logic."""

    @pytest.fixture
    def sample_pdf(self):
        """Create a 5-page sample PDF."""
        fd, path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        writer = pypdf.PdfWriter()
        for _ in range(5):
            writer.add_blank_page(width=612, height=792)
        with open(path, "wb") as f:
            writer.write(f)
        yield path
        if os.path.exists(path):
            os.remove(path)

    @pytest.mark.asyncio
    async def test_pipeline_initialization(self, sample_pdf):
        pipeline = PDFPipeline(task_id=1, file_path=sample_pdf)
        assert pipeline.task_id == 1
        assert pipeline.file_path == sample_pdf
        assert pipeline.context["status"] == FilePipelineStatus.PENDING
        assert pipeline.context["metadata"] == {}

    @pytest.mark.asyncio
    async def test_pipeline_execution_success(self):
        # Use storage utility to create the file
        task_id = 42
        file_path = save_upload_file(task_id, "original.pdf", b"pdf content")

        pipeline = PDFPipeline(task_id=task_id, file_path=file_path)

        async def mock_stage(context):
            context["metadata"]["mock_key"] = "mock_value"

        pipeline.add_stage(mock_stage)
        result = await pipeline.execute(cleanup=True)

        assert result["status"] == FilePipelineStatus.COMPLETED
        assert result["metadata"]["mock_key"] == "mock_value"
        # The file should be cleaned up
        assert not os.path.exists(file_path)

    @pytest.mark.asyncio
    async def test_pipeline_execution_failure(self, sample_pdf):
        pipeline = PDFPipeline(task_id=1, file_path=sample_pdf)

        async def failing_stage(context):
            raise RuntimeError("Stage failed")

        pipeline.add_stage(failing_stage)

        with pytest.raises(RuntimeError, match="Stage failed"):
            await pipeline.execute()

        assert pipeline.context["status"] == FilePipelineStatus.FAILED
        assert "Stage failed" in pipeline.context["error"]


class TestPDFPipelineStages:
    """Tests for individual pipeline stages."""

    @pytest.fixture
    def context(self, tmp_path):
        # Create a real PDF for the context
        pdf_path = tmp_path / "test.pdf"
        writer = pypdf.PdfWriter()
        writer.add_blank_page(width=612, height=792)
        writer.add_metadata({"/Title": "Test Title"})
        with open(pdf_path, "wb") as f:
            writer.write(f)

        return {"task_id": 1, "file_path": str(pdf_path), "metadata": {}}

    @pytest.mark.asyncio
    async def test_validate_and_extract_metadata_stage(self, context):
        await validate_and_extract_metadata_stage(context)

        assert "page_count" in context["metadata"]
        assert context["metadata"]["page_count"] == 1
        assert context["metadata"]["title"] == "Test Title"

    @pytest.mark.asyncio
    async def test_check_page_limit_stage_pass(self, context):
        context["metadata"]["page_count"] = 50
        # Should not raise
        await check_page_limit_stage(context)

    @pytest.mark.asyncio
    async def test_check_page_limit_stage_fail(self, context):
        context["metadata"]["page_count"] = 150  # Exceeds 100
        with pytest.raises(ValueError, match="PDF too large"):
            await check_page_limit_stage(context)

    @pytest.mark.asyncio
    async def test_validate_file_type_stage_pass(self, context):
        # file_path is already .pdf from fixture
        await validate_file_type_stage(context)

    @pytest.mark.asyncio
    async def test_validate_file_type_stage_fail(self, context):
        context["file_path"] = "test.txt"
        with pytest.raises(ValueError, match="Invalid file format"):
            await validate_file_type_stage(context)

    @pytest.mark.asyncio
    async def test_detect_handwriting_stage(self, context):
        from unittest.mock import patch

        with patch("app.utils.is_handwritten.is_handwritten", return_value=True):
            await detect_handwriting_stage(context)
            assert context["metadata"]["is_handwritten"] is True

        with patch("app.utils.is_handwritten.is_handwritten", return_value=False):
            await detect_handwriting_stage(context)
            assert context["metadata"]["is_handwritten"] is False

    @pytest.mark.asyncio
    async def test_extract_text_stage(self, context):
        from unittest.mock import AsyncMock, patch

        # Test digital path
        context["metadata"]["is_handwritten"] = False
        with patch(
            "app.services.ai_services.pdf_extraction_service.PDFExtractionService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.extract_text_from_formatted_pdf = AsyncMock(
                return_value="# Digital Content"
            )

            await extract_text_stage(context)

            mock_instance.extract_text_from_formatted_pdf.assert_called_once()
            assert context["markdown_content"] == "# Digital Content"

        # Test handwriting path
        context["metadata"]["is_handwritten"] = True
        with patch(
            "app.services.ai_services.pdf_extraction_service.PDFExtractionService"
        ) as MockService:
            mock_instance = MockService.return_value
            mock_instance.extract_handwritten_notes = AsyncMock(
                return_value="# Handwritten Content"
            )

            await extract_text_stage(context)

            mock_instance.extract_handwritten_notes.assert_called_once()
            assert context["markdown_content"] == "# Handwritten Content"

    @pytest.mark.asyncio
    async def test_save_markdown_stage(self, context):
        import shutil

        from app.utils.storage import RESULTS_BASE

        context["markdown_content"] = "# Extracted Markdown"
        try:
            await save_markdown_stage(context)

            file_path = context["metadata"]["markdown_file_path"]
            assert os.path.exists(file_path)
            with open(file_path) as f:
                assert f.read() == "# Extracted Markdown"
        finally:
            if RESULTS_BASE.exists():
                shutil.rmtree(RESULTS_BASE)
