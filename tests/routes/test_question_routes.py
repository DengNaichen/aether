"""
Tests for question.py routes

Tests cover:
- Getting next question for an owned graph
"""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.knowledge_graph import KnowledgeGraph
from app.models.knowledge_node import KnowledgeNode
from app.models.question import Question, QuestionDifficulty, QuestionType
from app.services.question_rec import NodeSelectionResult


class TestGetNextQuestionForOwnedGraph:
    """Test GET /me/graphs/{graph_id}/next-question endpoint"""

    @pytest.mark.asyncio
    async def test_get_next_question_no_questions_returns_none(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that empty graphs return a null question with a reason."""
        response = await authenticated_client.get(
            f"/me/graphs/{private_graph_in_db.id}/next-question"
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["question"] is None
        assert data["node_id"] is None
        assert data["selection_reason"] == "none_available"

    @pytest.mark.asyncio
    async def test_get_next_question_node_has_no_questions_returns_reason(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
        test_db: AsyncSession,
    ):
        """Test that a selected node with no questions returns node_has_no_questions."""
        node = KnowledgeNode(
            graph_id=private_graph_in_db.id,
            node_name="Limits",
        )
        test_db.add(node)
        await test_db.commit()
        await test_db.refresh(node)

        selection_result = NodeSelectionResult(
            knowledge_node=node,
            selection_reason="new_learning",
            priority_score=0.5,
        )

        with patch(
            "app.routes.question.QuestionService.select_next_node",
            new=AsyncMock(return_value=selection_result),
        ):
            response = await authenticated_client.get(
                f"/me/graphs/{private_graph_in_db.id}/next-question"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["question"] is None
        assert data["node_id"] == str(node.id)
        assert data["selection_reason"] == "node_has_no_questions"

    @pytest.mark.asyncio
    async def test_get_next_question_returns_multiple_choice(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
        test_db: AsyncSession,
    ):
        """Test that a selected node with questions returns a question."""
        node = KnowledgeNode(
            graph_id=private_graph_in_db.id,
            node_name="Derivatives",
        )
        test_db.add(node)
        await test_db.commit()
        await test_db.refresh(node)

        question = Question(
            graph_id=private_graph_in_db.id,
            node_id=node.id,
            question_type=QuestionType.MULTIPLE_CHOICE.value,
            text="What is the derivative of x^2?",
            details={
                "question_type": QuestionType.MULTIPLE_CHOICE.value,
                "options": ["x", "2x"],
                "correct_answer": 1,
                "p_g": 0.25,
                "p_s": 0.1,
            },
            difficulty=QuestionDifficulty.EASY.value,
        )
        test_db.add(question)
        await test_db.commit()
        await test_db.refresh(question)

        selection_result = NodeSelectionResult(
            knowledge_node=node,
            selection_reason="new_learning",
            priority_score=0.2,
        )

        with patch(
            "app.routes.question.QuestionService.select_next_node",
            new=AsyncMock(return_value=selection_result),
        ):
            response = await authenticated_client.get(
                f"/me/graphs/{private_graph_in_db.id}/next-question"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["node_id"] == str(node.id)
        assert data["selection_reason"] == "new_learning"
        assert data["question"]["question_id"] == str(question.id)
        assert data["question"]["question_type"] == "multiple_choice"
        assert data["question"]["knowledge_node_id"] == str(node.id)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("question_type", "details"),
        [
            (
                QuestionType.FILL_BLANK,
                {
                    "question_type": QuestionType.FILL_BLANK.value,
                    "expected_answer": ["Paris"],
                    "p_g": 0.0,
                    "p_s": 0.1,
                },
            ),
            (
                QuestionType.CALCULATION,
                {
                    "question_type": QuestionType.CALCULATION.value,
                    "expected_answer": ["4"],
                    "precision": 2,
                    "p_g": 0.0,
                    "p_s": 0.1,
                },
            ),
        ],
    )
    async def test_get_next_question_returns_other_types(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
        test_db: AsyncSession,
        question_type: QuestionType,
        details: dict,
    ):
        """Test that non-multiple-choice questions are converted correctly."""
        node = KnowledgeNode(
            graph_id=private_graph_in_db.id,
            node_name=f"{question_type.value} node",
        )
        test_db.add(node)
        await test_db.commit()
        await test_db.refresh(node)

        question = Question(
            graph_id=private_graph_in_db.id,
            node_id=node.id,
            question_type=question_type.value,
            text="Test prompt",
            details=details,
            difficulty=QuestionDifficulty.MEDIUM.value,
        )
        test_db.add(question)
        await test_db.commit()
        await test_db.refresh(question)

        selection_result = NodeSelectionResult(
            knowledge_node=node,
            selection_reason="new_learning",
            priority_score=0.1,
        )

        with patch(
            "app.routes.question.QuestionService.select_next_node",
            new=AsyncMock(return_value=selection_result),
        ):
            response = await authenticated_client.get(
                f"/me/graphs/{private_graph_in_db.id}/next-question"
            )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["node_id"] == str(node.id)
        assert data["question"]["question_id"] == str(question.id)
        assert data["question"]["question_type"] == question_type.value
        assert data["question"]["details"]["question_type"] == question_type.value

    @pytest.mark.asyncio
    async def test_get_next_question_service_error_returns_500(
        self,
        authenticated_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that unexpected errors surface as 500 responses."""
        with patch(
            "app.routes.question.QuestionService.select_next_node",
            new=AsyncMock(side_effect=RuntimeError("boom")),
        ):
            response = await authenticated_client.get(
                f"/me/graphs/{private_graph_in_db.id}/next-question"
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_get_next_question_not_owner_fails(
        self,
        other_user_client: AsyncClient,
        private_graph_in_db: KnowledgeGraph,
    ):
        """Test that non-owners cannot access the endpoint."""
        response = await other_user_client.get(
            f"/me/graphs/{private_graph_in_db.id}/next-question"
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert "owner" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_next_question_graph_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that missing graphs return 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await authenticated_client.get(f"/me/graphs/{fake_id}/next-question")

        assert response.status_code == status.HTTP_404_NOT_FOUND
