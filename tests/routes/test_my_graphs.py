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
    - Uploading files
"""

import uuid

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_graph import KnowledgeGraph
from app.models.user import User


@pytest_asyncio.fixture(scope="function")
async def user_in_db(test_db: AsyncSession) -> User:
    new_user = User(
        email=f"test.{uuid.uuid4().hex}@example.com",
        name="test user conf",
        is_active=True,
    )
    test_db.add(new_user)
    await test_db.commit()
    await test_db.refresh(new_user)
    return new_user


@pytest_asyncio.fixture(scope="function")
async def admin_in_db(test_db: AsyncSession) -> User:
    new_admin = User(
        email=f"admin.{uuid.uuid4().hex}@example.com",
        name="test admin conf",
        is_active=True,
        is_admin=True,
    )
    test_db.add(new_admin)
    await test_db.commit()
    await test_db.refresh(new_admin)
    return new_admin


@pytest_asyncio.fixture(scope="function")
async def other_user_in_db(test_db: AsyncSession) -> User:
    other_user = User(
        email=f"other.{uuid.uuid4().hex}@example.com",
        name="other test user",
        is_active=True,
    )
    test_db.add(other_user)
    await test_db.commit()
    await test_db.refresh(other_user)
    return other_user


class TestCreateKnowledgeGraph:
    """Test creating knowledge graphs"""

    @pytest.mark.asyncio
    async def test_create_graph_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
    ):
        """Test successfully creating a new graph"""
        graph_data = {
            "name": "Machine Learning Fundamentals",
            "description": "A comprehensive guide to machine learning basics",
            "tags": ["ml", "ai", "beginner"],
            "is_public": True,
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        # Verify response structure
        assert "id" in response_data
        assert "owner_id" in response_data
        assert "created_at" in response_data

        # Verify data
        assert response_data["name"] == graph_data["name"]
        assert response_data["slug"] == "machine-learning-fundamentals"
        assert response_data["description"] == graph_data["description"]
        assert response_data["tags"] == graph_data["tags"]
        assert response_data["is_public"] == graph_data["is_public"]

    @pytest.mark.asyncio
    async def test_create_graph_with_minimal_data(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a graph with only required fields"""
        graph_data = {
            "name": "Simple Graph",
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data["name"] == "Simple Graph"
        assert response_data["slug"] == "simple-graph"
        assert response_data["description"] is None
        assert response_data["tags"] == []
        assert response_data["is_public"] is False  # default value

    @pytest.mark.asyncio
    async def test_create_graph_with_duplicate_name_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that creating a graph with duplicate name/slug fails"""
        # Try to create a graph with the same name (will generate same slug)
        graph_data = {
            "name": "Private Test Graph",
            "description": "Duplicate attempt",
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_409_CONFLICT
        assert "already have a graph" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_create_graph_without_authentication_fails(
        self,
        client: AsyncClient,
    ):
        """Test that creating a graph without authentication fails"""
        graph_data = {
            "name": "Unauthorized Graph",
        }

        response = await client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_create_graph_with_empty_name_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that creating a graph with empty name fails"""
        graph_data = {
            "name": "",
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_graph_with_too_many_tags_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that creating a graph with more than 20 tags fails"""
        graph_data = {
            "name": "Too Many Tags",
            "tags": [f"tag_{i}" for i in range(21)],  # 21 tags
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == 422
        assert "Maximum 20 tags allowed" in str(response.json())

    @pytest.mark.asyncio
    async def test_create_graph_with_special_characters_in_name(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that special characters in name are properly slugified"""
        graph_data = {
            "name": "C++ Programming & Data Structures!",
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        # Slug should be sanitized
        assert response_data["name"] == "C++ Programming & Data Structures!"
        assert response_data["slug"] == "c-programming-data-structures"

    @pytest.mark.asyncio
    async def test_create_multiple_graphs_by_same_user(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that a user can create multiple graphs with different names"""
        graph_data_1 = {
            "name": "Graph One",
            "description": "First graph",
        }
        graph_data_2 = {
            "name": "Graph Two",
            "description": "Second graph",
        }

        response_1 = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data_1,
        )
        response_2 = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data_2,
        )

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED

        data_1 = response_1.json()
        data_2 = response_2.json()

        assert data_1["id"] != data_2["id"]
        assert data_1["slug"] == "graph-one"
        assert data_2["slug"] == "graph-two"

    @pytest.mark.asyncio
    async def test_create_graph_tags_are_normalized(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that tags are normalized (trimmed and lowercased)"""
        graph_data = {
            "name": "Tag Normalization Test",
            "tags": ["  Machine Learning  ", "AI", "  Deep-Learning  "],
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        # Tags should be trimmed and lowercased
        assert "machine learning" in response_data["tags"]
        assert "ai" in response_data["tags"]
        assert "deep-learning" in response_data["tags"]

    @pytest.mark.asyncio
    async def test_different_users_can_create_graphs_with_same_name(
        self,
        client: AsyncClient,
        user_in_db,
        admin_in_db,
    ):
        """Test that different users can create graphs with the same name"""
        from tests.conftest import create_access_token

        graph_data = {
            "name": "Common Graph Name",
            "description": "Same name, different owners",
        }

        # User creates a graph
        user_token = create_access_token(user_in_db.id)
        client.headers["Authorization"] = f"Bearer {user_token}"
        response_1 = await client.post(
            "/me/graphs/",
            json=graph_data,
        )

        # Admin creates a graph with same name
        admin_token = create_access_token(admin_in_db.id)
        client.headers["Authorization"] = f"Bearer {admin_token}"
        response_2 = await client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response_1.status_code == status.HTTP_201_CREATED
        assert response_2.status_code == status.HTTP_201_CREATED

        data_1 = response_1.json()
        data_2 = response_2.json()

        # Both should succeed with different IDs and owner_ids
        assert data_1["id"] != data_2["id"]
        assert data_1["owner_id"] != data_2["owner_id"]
        assert data_1["name"] == data_2["name"]
        assert data_1["slug"] == data_2["slug"]

    @pytest.mark.asyncio
    async def test_create_private_graph(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a private knowledge graph"""
        graph_data = {
            "name": "Private Research Notes",
            "description": "My personal research collection",
            "is_public": False,
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()

        assert response_data["is_public"] is False
        assert response_data["name"] == "Private Research Notes"

    @pytest.mark.asyncio
    async def test_create_graph_with_long_name(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that graph name length is validated"""
        # Test with name that exceeds maximum length (200 characters)
        long_name = "A" * 201
        graph_data = {
            "name": long_name,
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        # Should fail due to name length validation
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_graph_with_valid_long_name(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test creating a graph with maximum valid name length"""
        # Test with name at maximum length (200 characters)
        long_name = "A" * 200
        graph_data = {
            "name": long_name,
        }

        response = await authenticated_client.post(
            "/me/graphs/",
            json=graph_data,
        )

        # Should succeed
        assert response.status_code == status.HTTP_201_CREATED
        response_data = response.json()
        assert len(response_data["name"]) == 200


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

    @pytest.mark.asyncio
    async def test_get_my_graph_visualization_nonexistent_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that visualization returns 404 for missing graph"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.get(f"/me/graphs/{fake_id}/visualization")

        assert response.status_code == status.HTTP_404_NOT_FOUND


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
        assert data["graph"]["id"] == str(private_graph_in_db.id)

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

    @pytest.mark.asyncio
    async def test_get_my_graph_content_nonexistent_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that content returns 404 for missing graph"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.get(f"/me/graphs/{fake_id}/content")

        assert response.status_code == status.HTTP_404_NOT_FOUND


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

    @pytest.mark.asyncio
    async def test_enroll_in_my_graph_nonexistent_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that enrolling in missing graph returns 404"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.post(f"/me/graphs/{fake_id}/enrollments")

        assert response.status_code == status.HTTP_404_NOT_FOUND


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
        }

        response = await authenticated_client.post(
            "/me/graphs/invalid-uuid/import-structure",
            json=import_data,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_import_structure_graph_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test importing structure into missing graph"""
        import_data = {
            "nodes": [],
            "prerequisites": [],
        }

        response = await authenticated_client.post(
            "/me/graphs/00000000-0000-0000-0000-000000000000/import-structure",
            json=import_data,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


# class TestUploadFile:
#     """Test POST /me/graphs/{graph_id}/upload-file endpoint"""

#     @pytest.mark.asyncio
#     async def test_upload_file_invalid_file_type_fails(
#         self,
#         authenticated_client: AsyncClient,
#         private_graph_in_db: KnowledgeGraph,
#     ):
#         """Test that uploading unsupported file type fails"""
#         files = {"file": ("test.txt", b"not a pdf", "text/plain")}

#         response = await authenticated_client.post(
#             f"/me/graphs/{private_graph_in_db.id}/upload-file",
#             files=files,
#         )

#         assert response.status_code == status.HTTP_400_BAD_REQUEST
#         assert (
#             "Only PDF (.pdf) and Markdown (.md) files are supported."
#             in response.json()["detail"]
#         )

#     @pytest.mark.asyncio
#     async def test_upload_file_not_owner_fails(
#         self,
#         other_user_client: AsyncClient,
#         private_graph_in_db: KnowledgeGraph,
#     ):
#         """Test that non-owner cannot upload file"""
#         files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}

#         response = await other_user_client.post(
#             f"/me/graphs/{private_graph_in_db.id}/upload-file",
#             files=files,
#         )

#         assert response.status_code == status.HTTP_403_FORBIDDEN

#     @pytest.mark.asyncio
#     async def test_upload_file_nonexistent_graph_fails(
#         self,
#         authenticated_client: AsyncClient,
#     ):
#         """Test uploading file to nonexistent graph"""
#         fake_id = "00000000-0000-0000-0000-000000000000"
#         files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}

#         response = await authenticated_client.post(
#             f"/me/graphs/{fake_id}/upload-file",
#             files=files,
#         )

#         assert response.status_code == status.HTTP_404_NOT_FOUND

#     @pytest.mark.asyncio
#     async def test_upload_file_unauthenticated_fails(
#         self,
#         client: AsyncClient,
#         private_graph_in_db: KnowledgeGraph,
#     ):
#         """Test that upload requires authentication"""
#         files = {"file": ("test.pdf", b"fake pdf content", "application/pdf")}

#         response = await client.post(
#             f"/me/graphs/{private_graph_in_db.id}/upload-file",
#             files=files,
#         )

#         assert response.status_code == status.HTTP_401_UNAUTHORIZED
