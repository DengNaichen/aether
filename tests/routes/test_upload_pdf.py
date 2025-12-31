"""
Tests for the PDF upload endpoint: POST /me/graphs/{graph_id}/upload-pdf

These tests verify the upload_pdf route functionality including:
- File validation
- Pipeline execution with mocked AI services
- Error handling
"""

import io
import shutil
from unittest.mock import AsyncMock, patch

import pypdf
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.deps import get_current_active_user, get_db, get_owned_graph
from app.main import app
from app.models.knowledge_graph import KnowledgeGraph
from app.models.user import User
from app.utils.storage import RESULTS_BASE, STORAGE_BASE


@pytest_asyncio.fixture(scope="function")
async def mock_user():
    """Create a mock user for testing."""
    user = User(
        id="12345678-1234-1234-1234-123456789abc",
        email="test@example.com",
        name="Test User",
        is_active=True,
    )
    return user


@pytest_asyncio.fixture(scope="function")
async def mock_graph(mock_user):
    """Create a mock knowledge graph for testing."""
    graph = KnowledgeGraph(
        id="87654321-4321-4321-4321-cba987654321",
        owner_id=mock_user.id,
        name="Test Graph",
        slug="test-graph",
        description="Test graph for PDF upload",
        is_public=False,
    )
    return graph


@pytest_asyncio.fixture(scope="function")
async def test_client(mock_user, mock_graph):
    """Create a test client with mocked dependencies."""

    async def override_get_current_active_user():
        return mock_user

    async def override_get_owned_graph():
        return mock_graph

    async def override_get_db():
        # We don't need a real DB for these tests
        yield None

    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    app.dependency_overrides[get_owned_graph] = override_get_owned_graph
    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Cleanup
    del app.dependency_overrides[get_current_active_user]
    del app.dependency_overrides[get_owned_graph]
    del app.dependency_overrides[get_db]


@pytest.fixture
def sample_pdf_bytes():
    """Create a sample PDF in memory."""
    buffer = io.BytesIO()
    writer = pypdf.PdfWriter()
    for _ in range(3):
        writer.add_blank_page(width=612, height=792)
    writer.write(buffer)
    buffer.seek(0)
    return buffer.read()


@pytest.fixture
def cleanup_storage():
    """Cleanup storage directories after tests."""
    yield
    # Clean up any created storage directories
    if STORAGE_BASE.exists():
        shutil.rmtree(STORAGE_BASE)
    if RESULTS_BASE.exists():
        shutil.rmtree(RESULTS_BASE)


class TestUploadPDFEndpoint:
    """Tests for the upload_pdf endpoint."""

    @pytest.mark.asyncio
    async def test_upload_pdf_rejects_non_pdf_file(
        self, test_client: AsyncClient, mock_graph
    ):
        """Test that non-PDF files are rejected."""
        response = await test_client.post(
            f"/me/graphs/{mock_graph.id}/upload-pdf",
            files={"file": ("test.txt", b"not a pdf", "text/plain")},
        )

        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_pdf_rejects_file_without_extension(
        self, test_client: AsyncClient, mock_graph
    ):
        """Test that files without .pdf extension are rejected."""
        response = await test_client.post(
            f"/me/graphs/{mock_graph.id}/upload-pdf",
            files={
                "file": ("noextension", b"some content", "application/octet-stream")
            },
        )

        assert response.status_code == 400
        assert "Only PDF files are supported" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_pdf_success(
        self, test_client: AsyncClient, mock_graph, sample_pdf_bytes, cleanup_storage
    ):
        """Test successful PDF upload and extraction."""
        # Mock the extraction stages
        with (
            patch(
                "app.services.pdf_pipeline.detect_handwriting_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx["metadata"].update(
                        {"is_handwritten": False}
                    )
                ),
            ),
            patch(
                "app.services.pdf_pipeline.extract_text_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx.update(
                        {
                            "markdown_content": "# Extracted Content\n\nThis is the content."
                        }
                    )
                ),
            ),
        ):
            response = await test_client.post(
                f"/me/graphs/{mock_graph.id}/upload-pdf",
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()

        assert data["status"] == "completed"
        assert data["graph_id"] == str(mock_graph.id)
        assert "task_id" in data
        assert "metadata" in data
        assert data["message"] == "PDF extracted successfully"

    @pytest.mark.asyncio
    async def test_upload_pdf_saves_to_graph_dir(
        self, test_client: AsyncClient, mock_graph, sample_pdf_bytes, cleanup_storage
    ):
        """Test that markdown is saved in the graph-specific directory."""
        with (
            patch(
                "app.services.pdf_pipeline.detect_handwriting_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx["metadata"].update(
                        {"is_handwritten": False}
                    )
                ),
            ),
            patch(
                "app.services.pdf_pipeline.extract_text_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx.update(
                        {"markdown_content": "# Content"}
                    )
                ),
            ),
        ):
            response = await test_client.post(
                f"/me/graphs/{mock_graph.id}/upload-pdf",
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()

        # Verify the path contains the graph ID
        expected_path_part = f"graph_{mock_graph.id}"
        assert expected_path_part in data["markdown_file_path"]
        assert (
            "task_" not in data["markdown_file_path"].split("/")[-1]
        )  # Filename should be timestamped, not task_id based folder structure for file itself (though it is in graph folder)

    @pytest.mark.asyncio
    async def test_upload_pdf_validates_metadata(
        self, test_client: AsyncClient, mock_graph, sample_pdf_bytes, cleanup_storage
    ):
        """Test that PDF metadata is extracted and included in response."""
        with (
            patch(
                "app.services.pdf_pipeline.detect_handwriting_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx["metadata"].update(
                        {"is_handwritten": False}
                    )
                ),
            ),
            patch(
                "app.services.pdf_pipeline.extract_text_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx.update(
                        {"markdown_content": "# Content"}
                    )
                ),
            ),
        ):
            response = await test_client.post(
                f"/me/graphs/{mock_graph.id}/upload-pdf",
                files={"file": ("multipage.pdf", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()

        # Check that page_count is in metadata
        assert "page_count" in data["metadata"]
        assert data["metadata"]["page_count"] == 3  # Our sample PDF has 3 pages

    @pytest.mark.asyncio
    async def test_upload_pdf_handles_extraction_error(
        self, test_client: AsyncClient, mock_graph, sample_pdf_bytes, cleanup_storage
    ):
        """Test that extraction errors are handled properly."""
        with (
            patch(
                "app.services.pdf_pipeline.detect_handwriting_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx["metadata"].update(
                        {"is_handwritten": False}
                    )
                ),
            ),
            patch(
                "app.services.pdf_pipeline.extract_text_stage",
                new=AsyncMock(side_effect=RuntimeError("AI service unavailable")),
            ),
        ):
            response = await test_client.post(
                f"/me/graphs/{mock_graph.id}/upload-pdf",
                files={"file": ("test.pdf", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 500
        assert "AI service unavailable" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_pdf_page_limit_exceeded(
        self, test_client: AsyncClient, mock_graph, cleanup_storage
    ):
        """Test that PDFs exceeding page limit are rejected."""
        # Create a PDF with 101 pages (exceeds default 100 page limit)
        buffer = io.BytesIO()
        writer = pypdf.PdfWriter()
        for _ in range(101):
            writer.add_blank_page(width=612, height=792)
        writer.write(buffer)
        buffer.seek(0)
        large_pdf_bytes = buffer.read()

        response = await test_client.post(
            f"/me/graphs/{mock_graph.id}/upload-pdf",
            files={"file": ("large.pdf", large_pdf_bytes, "application/pdf")},
        )

        assert response.status_code == 400
        assert "PDF too large" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_pdf_handwritten_detection(
        self, test_client: AsyncClient, mock_graph, sample_pdf_bytes, cleanup_storage
    ):
        """Test that handwritten content is detected and handled."""
        with (
            patch(
                "app.services.pdf_pipeline.detect_handwriting_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx["metadata"].update(
                        {"is_handwritten": True}
                    )
                ),
            ),
            patch(
                "app.services.pdf_pipeline.extract_text_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx.update(
                        {"markdown_content": "# Handwritten Notes"}
                    )
                ),
            ),
        ):
            response = await test_client.post(
                f"/me/graphs/{mock_graph.id}/upload-pdf",
                files={"file": ("notes.pdf", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 201
        data = response.json()

        assert data["metadata"]["is_handwritten"] is True


class TestUploadPDFEdgeCases:
    """Edge case tests for the upload_pdf endpoint."""

    @pytest.mark.asyncio
    async def test_upload_pdf_with_empty_filename(
        self, test_client: AsyncClient, mock_graph
    ):
        """Test behavior with empty filename."""
        response = await test_client.post(
            f"/me/graphs/{mock_graph.id}/upload-pdf",
            files={"file": ("", b"content", "application/pdf")},
        )

        # Either 400 (our validation) or 422 (FastAPI validation) is acceptable
        assert response.status_code in (400, 422)

    @pytest.mark.asyncio
    async def test_upload_pdf_case_insensitive_extension(
        self, test_client: AsyncClient, mock_graph, sample_pdf_bytes, cleanup_storage
    ):
        """Test that .PDF (uppercase) is also accepted."""
        with (
            patch(
                "app.services.pdf_pipeline.detect_handwriting_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx["metadata"].update(
                        {"is_handwritten": False}
                    )
                ),
            ),
            patch(
                "app.services.pdf_pipeline.extract_text_stage",
                new=AsyncMock(
                    side_effect=lambda ctx: ctx.update(
                        {"markdown_content": "# Content"}
                    )
                ),
            ),
        ):
            response = await test_client.post(
                f"/me/graphs/{mock_graph.id}/upload-pdf",
                files={"file": ("TEST.PDF", sample_pdf_bytes, "application/pdf")},
            )

        assert response.status_code == 201
