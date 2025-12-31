"""
Tests for my_graphs.py routes

Tests cover:
- Getting all user's graphs
- Getting a specific graph
- Getting graph visualization
- Getting graph content
- Creating graphs
- Enrolling in own graph
- Importing graph structure
- Uploading PDFs
"""

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.knowledge_graph import KnowledgeGraph


class TestGetMyGraphs:
    """Test GET /me/graphs/ endpoint"""

    @pytest.mark.asyncio
    async def test_get_my_graphs_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test getting all graphs owned by the user"""
        response = await authenticated_client.get("/me/graphs/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our graph
        graph = next((g for g in data if g["id"] == str(private_graph_in_db.id)), None)
        assert graph is not None
        assert graph["name"] == "Private Test Graph"

    @pytest.mark.asyncio
    async def test_get_my_graphs_empty_list(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting graphs when user has none"""
        response = await authenticated_client.get("/me/graphs/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_my_graphs_without_auth_fails(
        self,
        client: AsyncClient,
    ):
        """Test that getting graphs without auth fails"""
        response = await client.get("/me/graphs/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestGetMyGraph:
    """Test GET /me/graphs/{graph_id} endpoint"""

    @pytest.mark.asyncio
    async def test_get_my_graph_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test getting a specific graph owned by the user"""
        response = await authenticated_client.get(
            f"/me/graphs/{private_graph_in_db.id}"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(private_graph_in_db.id)
        assert data["name"] == "Private Test Graph"

    @pytest.mark.asyncio
    async def test_get_my_graph_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting another user's graph fails"""
        response = await other_user_client.get(f"/me/graphs/{private_graph_in_db.id}")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_get_my_graph_nonexistent_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test getting a graph that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.get(f"/me/graphs/{fake_id}")

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestGetMyGraphVisualization:
    """Test GET /me/graphs/{graph_id}/visualization endpoint"""

    @pytest.mark.asyncio
    async def test_get_my_graph_visualization_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test getting visualization of owned graph"""
        response = await authenticated_client.get(
            f"/me/graphs/{private_graph_in_db.id}/visualization"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    @pytest.mark.asyncio
    async def test_get_my_graph_visualization_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting visualization of another user's graph fails"""
        response = await other_user_client.get(
            f"/me/graphs/{private_graph_in_db.id}/visualization"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetMyGraphContent:
    """Test GET /me/graphs/{graph_id}/content endpoint"""

    @pytest.mark.asyncio
    async def test_get_my_graph_content_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test getting content of owned graph"""
        response = await authenticated_client.get(
            f"/me/graphs/{private_graph_in_db.id}/content"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "graph" in data
        assert "nodes" in data
        assert "prerequisites" in data

    @pytest.mark.asyncio
    async def test_get_my_graph_content_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting content of another user's graph fails"""
        response = await other_user_client.get(
            f"/me/graphs/{private_graph_in_db.id}/content"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestEnrollInMyGraph:
    """Test POST /me/graphs/{graph_id}/enrollments endpoint"""

    @pytest.mark.asyncio
    async def test_enroll_in_my_graph_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test owner enrolling in their own graph"""
        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/enrollments"
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["graph_id"] == str(private_graph_in_db.id)
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_enroll_in_my_graph_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that non-owner cannot enroll via this endpoint"""
        response = await other_user_client.post(
            f"/me/graphs/{private_graph_in_db.id}/enrollments"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_enroll_in_my_graph_twice_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
        graph_enrollment_owner_in_db,
    ):
        """Test that enrolling twice fails"""
        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/enrollments"
        )

        assert response.status_code == status.HTTP_409_CONFLICT


class TestImportStructure:
    """Test POST /me/graphs/{graph_id}/import-structure endpoint"""

    @pytest.mark.asyncio
    async def test_import_structure_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test successfully importing graph structure"""
        import_data = {
            "nodes": [
                {
                    "node_id_str": "node1",
                    "node_name": "Node 1",
                    "description": "First node",
                },
                {
                    "node_id_str": "node2",
                    "node_name": "Node 2",
                    "description": "Second node",
                },
            ],
            "prerequisites": [
                {
                    "from_node_id_str": "node1",
                    "to_node_id_str": "node2",
                    "weight": 1.0,
                }
            ],
        }

        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/import-structure",
            json=import_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["nodes_created"] == 2
        assert data["prerequisites_created"] == 1

    @pytest.mark.asyncio
    async def test_import_structure_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that non-owner cannot import structure"""
        import_data = {
            "nodes": [],
            "prerequisites": [],
            "subtopics": [],
        }

        response = await other_user_client.post(
            f"/me/graphs/{private_graph_in_db.id}/import-structure",
            json=import_data,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_import_structure_invalid_graph_id_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test importing with invalid graph ID"""
        import_data = {
            "nodes": [],
            "prerequisites": [],
            "subtopics": [],
        }

        response = await authenticated_client.post(
            "/me/graphs/invalid-uuid/import-structure",
            json=import_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST


class TestUploadPDF:
    """Test POST /me/graphs/{graph_id}/upload-pdf endpoint"""

    @pytest.mark.asyncio
    async def test_upload_pdf_invalid_file_type_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that uploading non-PDF file fails"""
        files = {"file": ("test.txt", b"not a pdf", "text/plain")}

        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/upload-pdf",
            files=files,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "PDF" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_pdf_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that non-owner cannot upload PDF"""
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}

        response = await other_user_client.post(
            f"/me/graphs/{private_graph_in_db.id}/upload-pdf",
            files=files,
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_upload_pdf_nonexistent_graph_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test uploading PDF to nonexistent graph"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}

        response = await authenticated_client.post(
            f"/me/graphs/{fake_id}/upload-pdf",
            files=files,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
