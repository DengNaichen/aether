"""
Tests for answer.py routes

Tests cover:
- Submitting answers
- Error handling
"""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from httpx import AsyncClient

from app.models.question import Question


class TestSubmitSingleAnswer:
    """Test POST /answer endpoint."""

    @pytest.mark.asyncio
    async def test_submit_answer_success(
        self,
        authenticated_client: AsyncClient,
        question_in_db: Question,
    ):
        """Test successful answer submission and grading."""
        payload = {
            "question_id": str(question_in_db.id),
            "graph_id": str(question_in_db.graph_id),
            "user_answer": {
                "question_type": "multiple_choice",
                "selected_option": question_in_db.details["correct_answer"],
            },
        }

        response = await authenticated_client.post("/answer", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["is_correct"] is True
        assert data["mastery_updated"] is True
        assert "answer_id" in data
        assert data["correct_answer"]["question_type"] == "multiple_choice"
        assert (
            data["correct_answer"]["selected_option"]
            == question_in_db.details["correct_answer"]
        )

    @pytest.mark.asyncio
    async def test_submit_answer_question_not_found(
        self,
        authenticated_client: AsyncClient,
    ):
        """Test that submitting a non-existent question returns 404."""
        payload = {
            "question_id": str(uuid4()),
            "graph_id": str(uuid4()),
            "user_answer": {
                "question_type": "multiple_choice",
                "selected_option": 0,
            },
        }

        response = await authenticated_client.post("/answer", json=payload)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_submit_answer_mastery_update_failure(
        self,
        authenticated_client: AsyncClient,
        question_in_db: Question,
    ):
        """Test that mastery update errors still return a response."""
        payload = {
            "question_id": str(question_in_db.id),
            "graph_id": str(question_in_db.graph_id),
            "user_answer": {
                "question_type": "multiple_choice",
                "selected_option": question_in_db.details["correct_answer"],
            },
        }

        with patch(
            "app.routes.answer.MasteryService.update_mastery_from_grading",
            new=AsyncMock(side_effect=Exception("boom")),
        ):
            response = await authenticated_client.post("/answer", json=payload)

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["mastery_updated"] is False
        assert data["is_correct"] is True

    @pytest.mark.asyncio
    async def test_submit_answer_unauthenticated_fails(
        self,
        client: AsyncClient,
        question_in_db: Question,
    ):
        """Test that submitting without auth is rejected."""
        payload = {
            "question_id": str(question_in_db.id),
            "graph_id": str(question_in_db.graph_id),
            "user_answer": {
                "question_type": "multiple_choice",
                "selected_option": 0,
            },
        }

        response = await client.post("/answer", json=payload)

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
