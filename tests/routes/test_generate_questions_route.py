"""
Tests for the generate-questions endpoint in my_graphs.py

Tests cover:
- Successful question generation
- Authentication requirements
- Authorization (only owner can generate)
- Error handling for service failures
- Request validation
"""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_graph import KnowledgeGraph
from app.models.user import User


# ==================== Local Fixtures ====================


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


# ==================== Test Class ====================


class TestGenerateQuestionsRoute:
    """Test POST /me/graphs/{graph_id}/generate-questions endpoint"""

    @pytest.mark.asyncio
    async def test_generate_questions_success(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test successful question generation"""
        mock_stats = {
            "nodes_processed": 5,
            "nodes_skipped": 1,
            "questions_generated": 15,
            "questions_saved": 15,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={
                    "questions_per_node": 3,
                    "question_types": ["multiple_choice"],
                    "only_nodes_without_questions": True,
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["nodes_processed"] == 5
            assert data["questions_generated"] == 15
            assert data["questions_saved"] == 15

            # Verify the service was called with correct parameters
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["graph_id"] == str(private_graph_in_db.id)
            assert call_kwargs["questions_per_node"] == 3
            assert call_kwargs["question_types"] == ["multiple_choice"]
            assert call_kwargs["only_nodes_without_questions"] is True

    @pytest.mark.asyncio
    async def test_generate_questions_with_defaults(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test question generation with default parameters"""
        mock_stats = {
            "nodes_processed": 3,
            "nodes_skipped": 0,
            "questions_generated": 9,
            "questions_saved": 9,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            # Send request with empty body (use defaults)
            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={},
            )

            assert response.status_code == status.HTTP_200_OK

            # Verify defaults were used
            mock_generate.assert_called_once()
            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["questions_per_node"] == 3  # default
            assert call_kwargs["question_types"] == ["multiple_choice"]  # default
            assert call_kwargs["only_nodes_without_questions"] is True  # default

    @pytest.mark.asyncio
    async def test_generate_questions_with_all_question_types(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test question generation with all question types"""
        mock_stats = {
            "nodes_processed": 2,
            "nodes_skipped": 0,
            "questions_generated": 6,
            "questions_saved": 6,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={
                    "question_types": ["multiple_choice", "fill_blank", "short_answer"],
                },
            )

            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_generate_questions_with_difficulty_distribution(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test question generation with custom difficulty distribution"""
        mock_stats = {
            "nodes_processed": 1,
            "nodes_skipped": 0,
            "questions_generated": 5,
            "questions_saved": 5,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={
                    "questions_per_node": 5,
                    "difficulty_distribution": {"easy": 2, "medium": 2, "hard": 1},
                },
            )

            assert response.status_code == status.HTTP_200_OK

            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["difficulty_distribution"] == {
                "easy": 2,
                "medium": 2,
                "hard": 1,
            }

    @pytest.mark.asyncio
    async def test_generate_questions_with_user_guidance(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test question generation with custom user guidance"""
        mock_stats = {
            "nodes_processed": 1,
            "nodes_skipped": 0,
            "questions_generated": 3,
            "questions_saved": 3,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={
                    "user_guidance": "Focus on practical applications and real-world examples",
                },
            )

            assert response.status_code == status.HTTP_200_OK

            call_kwargs = mock_generate.call_args.kwargs
            assert (
                "practical applications"
                in call_kwargs["user_guidance"]
            )

    @pytest.mark.asyncio
    async def test_generate_questions_include_nodes_with_questions(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test generating questions for nodes that already have questions"""
        mock_stats = {
            "nodes_processed": 10,
            "nodes_skipped": 0,
            "questions_generated": 30,
            "questions_saved": 30,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={
                    "only_nodes_without_questions": False,
                },
            )

            assert response.status_code == status.HTTP_200_OK

            call_kwargs = mock_generate.call_args.kwargs
            assert call_kwargs["only_nodes_without_questions"] is False

    @pytest.mark.asyncio
    async def test_generate_questions_unauthenticated_fails(
        self,
        client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that unauthenticated users cannot generate questions"""
        response = await client.post(
            f"/me/graphs/{private_graph_in_db.id}/generate-questions",
            json={},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_generate_questions_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that non-owners cannot generate questions"""
        response = await other_user_client.post(
            f"/me/graphs/{private_graph_in_db.id}/generate-questions",
            json={},
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.asyncio
    async def test_generate_questions_graph_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test generating questions for non-existent graph"""
        fake_id = "00000000-0000-0000-0000-000000000000"

        response = await authenticated_client.post(
            f"/me/graphs/{fake_id}/generate-questions",
            json={},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_generate_questions_service_error(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test error handling when service fails"""
        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.side_effect = Exception("LLM service unavailable")

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={},
            )

            assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Question generation failed" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_generate_questions_invalid_questions_per_node(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test validation for questions_per_node parameter"""
        # Test too low
        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/generate-questions",
            json={"questions_per_node": 0},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Test too high
        response = await authenticated_client.post(
            f"/me/graphs/{private_graph_in_db.id}/generate-questions",
            json={"questions_per_node": 11},
        )
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_generate_questions_valid_boundary_values(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test boundary values for questions_per_node"""
        mock_stats = {
            "nodes_processed": 1,
            "nodes_skipped": 0,
            "questions_generated": 1,
            "questions_saved": 1,
            "errors": [],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            # Test minimum (1)
            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={"questions_per_node": 1},
            )
            assert response.status_code == status.HTTP_200_OK

            # Test maximum (10)
            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={"questions_per_node": 10},
            )
            assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_generate_questions_partial_failure_returns_stats(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that partial failures are reported in statistics"""
        mock_stats = {
            "nodes_processed": 8,
            "nodes_skipped": 2,
            "questions_generated": 24,
            "questions_saved": 22,
            "errors": [
                "Failed to save questions for Node X",
                "No questions generated for Node Y",
            ],
        }

        with patch(
            "app.routes.my_graphs.generate_questions_for_graph",
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = mock_stats

            response = await authenticated_client.post(
                f"/me/graphs/{private_graph_in_db.id}/generate-questions",
                json={},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["nodes_processed"] == 8
            assert data["nodes_skipped"] == 2
            assert data["questions_generated"] == 24
            assert data["questions_saved"] == 22
            assert len(data["errors"]) == 2
