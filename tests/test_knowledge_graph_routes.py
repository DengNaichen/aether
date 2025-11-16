import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.models.knowledge_graph import KnowledgeGraph


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
        from app.core.security import create_access_token

        graph_data = {
            "name": "Common Graph Name",
            "description": "Same name, different owners",
        }

        # User creates a graph
        user_token = create_access_token(user_in_db)
        client.headers["Authorization"] = f"Bearer {user_token}"
        response_1 = await client.post(
            "/me/graphs/",
            json=graph_data,
        )

        # Admin creates a graph with same name
        admin_token = create_access_token(admin_in_db)
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
