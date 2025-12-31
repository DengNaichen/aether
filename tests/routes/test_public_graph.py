"""
Tests for public_graph.py routes

Tests cover:
- Getting template graphs
- Enrolling in public/template graphs
- Getting graph details
- Getting next question
- Getting visualization
- Getting graph content
"""

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enrollment import GraphEnrollment
from app.models.knowledge_graph import KnowledgeGraph
from app.models.user import User


class TestGetTemplateGraphs:
    """Test GET /graphs/templates endpoint"""

    @pytest.mark.asyncio
    async def test_get_template_graphs_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Test successfully getting all template graphs"""
        response = await authenticated_client.get("/graphs/templates")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

        # Find our template graph
        template = next(
            (g for g in data if g["id"] == str(template_graph_in_db.id)), None
        )
        assert template is not None
        assert template["is_template"] is True
        assert template["name"] == "Official Calculus Template"

    @pytest.mark.asyncio
    async def test_get_template_graphs_shows_enrollment_status(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
        graph_enrollment_student_in_db: GraphEnrollment,
    ):
        """Test that template graphs show enrollment status"""
        response = await authenticated_client.get("/graphs/templates")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        template = next(
            (g for g in data if g["id"] == str(template_graph_in_db.id)), None
        )
        assert template is not None
        assert template["is_enrolled"] is True

    @pytest.mark.asyncio
    async def test_get_template_graphs_without_auth_succeeds(
        self,
        client: AsyncClient,
    ):
        """Test that getting templates without auth succeeds (endpoint uses optional auth)"""
        response = await client.get("/graphs/templates")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)


class TestEnrollInTemplateGraph:
    """Test POST /graphs/{graph_id}/enrollments endpoint"""

    @pytest.mark.asyncio
    async def test_enroll_in_template_graph_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Test successfully enrolling in a template graph"""
        response = await authenticated_client.post(
            f"/graphs/{template_graph_in_db.id}/enrollments"
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["graph_id"] == str(template_graph_in_db.id)
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_enroll_in_public_graph_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test enrolling in a public (non-template) graph"""
        # Create a public graph
        public_graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Public Graph",
            slug="public-graph",
            is_public=True,
            is_template=False,
        )
        test_db.add(public_graph)
        await test_db.commit()
        await test_db.refresh(public_graph)

        response = await authenticated_client.post(
            f"/graphs/{public_graph.id}/enrollments"
        )

        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.asyncio
    async def test_enroll_in_private_graph_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that enrolling in a private graph fails"""
        response = await authenticated_client.post(
            f"/graphs/{private_graph_in_db.id}/enrollments"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "private" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_enroll_in_nonexistent_graph_fails(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test enrolling in a graph that doesn't exist"""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.post(f"/graphs/{fake_id}/enrollments")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_enroll_twice_fails(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
        graph_enrollment_student_in_db: GraphEnrollment,
    ):
        """Test that enrolling twice in the same graph fails"""
        response = await authenticated_client.post(
            f"/graphs/{template_graph_in_db.id}/enrollments"
        )

        assert response.status_code == status.HTTP_409_CONFLICT


class TestGetTemplateGraphDetails:
    """Test GET /graphs/{graph_id}/ endpoint"""

    @pytest.mark.asyncio
    async def test_get_template_graph_details_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Test getting details of a template graph"""
        response = await authenticated_client.get(f"/graphs/{template_graph_in_db.id}/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["id"] == str(template_graph_in_db.id)
        assert data["name"] == "Official Calculus Template"
        assert data["is_template"] is True

    @pytest.mark.asyncio
    async def test_get_public_graph_details_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test getting details of a public graph"""
        public_graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Public Graph",
            slug="public-graph",
            is_public=True,
        )
        test_db.add(public_graph)
        await test_db.commit()
        await test_db.refresh(public_graph)

        response = await authenticated_client.get(f"/graphs/{public_graph.id}/")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_private_graph_details_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting private graph details fails"""
        response = await authenticated_client.get(f"/graphs/{private_graph_in_db.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetNextQuestionInEnrolledGraph:
    """Test GET /graphs/{graph_id}/next-question endpoint"""

    @pytest.mark.asyncio
    async def test_get_next_question_not_enrolled_fails(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting next question without enrollment fails"""
        response = await authenticated_client.get(
            f"/graphs/{template_graph_in_db.id}/next-question"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not enrolled" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_next_question_private_graph_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting next question from private graph fails"""
        response = await authenticated_client.get(
            f"/graphs/{private_graph_in_db.id}/next-question"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "not ready for public use" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_next_question_enrolled_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
        graph_enrollment_student_in_db: GraphEnrollment,
    ):
        """Test getting next question when enrolled (may return no question if graph is empty)"""
        response = await authenticated_client.get(
            f"/graphs/{template_graph_in_db.id}/next-question"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Graph might be empty, so question could be None
        assert "selection_reason" in data


class TestGetGraphVisualization:
    """Test GET /graphs/{graph_id}/visualization endpoint"""

    @pytest.mark.asyncio
    async def test_get_visualization_template_graph_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Test getting visualization for a template graph"""
        response = await authenticated_client.get(
            f"/graphs/{template_graph_in_db.id}/visualization"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "nodes" in data
        assert "edges" in data

    @pytest.mark.asyncio
    async def test_get_visualization_public_graph_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test getting visualization for a public graph"""
        public_graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Public Graph",
            slug="public-graph",
            is_public=True,
        )
        test_db.add(public_graph)
        await test_db.commit()
        await test_db.refresh(public_graph)

        response = await authenticated_client.get(
            f"/graphs/{public_graph.id}/visualization"
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_visualization_enrolled_graph_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
        graph_enrollment_student_in_db: GraphEnrollment,
    ):
        """Test getting visualization for an enrolled graph"""
        response = await authenticated_client.get(
            f"/graphs/{template_graph_in_db.id}/visualization"
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_visualization_private_not_enrolled_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting visualization of private graph without enrollment fails"""
        response = await other_user_client.get(
            f"/graphs/{private_graph_in_db.id}/visualization"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestGetPublicGraphContent:
    """Test GET /graphs/{graph_id}/content endpoint"""

    @pytest.mark.asyncio
    async def test_get_content_template_graph_success(
        self,
        authenticated_client: AsyncClient,
        template_graph_in_db: KnowledgeGraph,
    ):
        """Test getting content of a template graph"""
        response = await authenticated_client.get(
            f"/graphs/{template_graph_in_db.id}/content"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "graph" in data
        assert "nodes" in data
        assert "prerequisites" in data

    @pytest.mark.asyncio
    async def test_get_content_public_graph_success(
        self,
        authenticated_client: AsyncClient,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test getting content of a public graph"""
        public_graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Public Graph",
            slug="public-graph",
            is_public=True,
        )
        test_db.add(public_graph)
        await test_db.commit()
        await test_db.refresh(public_graph)

        response = await authenticated_client.get(f"/graphs/{public_graph.id}/content")

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_get_content_private_graph_fails(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that getting content of private graph fails"""
        response = await authenticated_client.get(
            f"/graphs/{private_graph_in_db.id}/content"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "private" in response.json()["detail"].lower()
