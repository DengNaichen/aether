"""
Unit tests for grading handlers in app/worker/handlers.py

This module tests the grading functionality including:
- grade_answer() and its helper functions
- handle_grade_submission() and its helper functions
"""
import asyncio
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, AsyncMock, Mock
from uuid import UUID

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

import app.models.neo4j_model as neo
from app.models.quiz import QuizAttempt, QuizStatus, SubmissionAnswer
from app.worker.config import WorkerContext
from app.worker.handlers import (
    _calculate_final_score,
    _validate_grading_payload,
    handle_grade_submission,
)
# =============================================================================
# Test Payload Validation
# =============================================================================


@pytest.mark.asyncio
class TestGradingPayloadValidation:
    """Test suite for _validate_grading_payload function."""

    def test_validate_payload_success(self):
        """Test validation with a valid payload."""
        submission_id = uuid.uuid4()
        user_id = uuid.uuid4()

        payload = {
            "submission_id": str(submission_id),
            "user_id": str(user_id)
        }

        result_submission_id, result_user_id = _validate_grading_payload(payload)

        assert result_submission_id == submission_id
        assert result_user_id == str(user_id)

    def test_validate_payload_missing_submission_id(self):
        """Test validation with missing submission_id."""
        payload = {"user_id": str(uuid.uuid4())}

        result_submission_id, result_user_id = _validate_grading_payload(payload)

        assert result_submission_id is None
        assert result_user_id is None

    def test_validate_payload_missing_user_id(self):
        """Test validation with missing user_id."""
        payload = {"submission_id": str(uuid.uuid4())}

        result_submission_id, result_user_id = _validate_grading_payload(payload)

        assert result_submission_id is None
        assert result_user_id is None

    def test_validate_payload_invalid_uuid_format(self):
        """Test validation with invalid UUID format."""
        payload = {
            "submission_id": "not-a-valid-uuid",
            "user_id": str(uuid.uuid4())
        }

        result_submission_id, result_user_id = _validate_grading_payload(payload)

        assert result_submission_id is None
        assert result_user_id is None

    def test_validate_payload_empty_dict(self):
        """Test validation with empty payload."""
        payload = {}

        result_submission_id, result_user_id = _validate_grading_payload(payload)

        assert result_submission_id is None
        assert result_user_id is None


# =============================================================================
# Test Mastery Level Update and Score Calculation
# =============================================================================


@pytest.mark.asyncio
class TestMasteryLevelUpdate:
    """Test suite for _update_mastery_level and _calculate_final_score function.
    """

    def test_calculate_final_score_perfect(self):
        """Test calculating final score with all correct answers."""
        score = _calculate_final_score(10, 10)
        assert score == 100

    def test_calculate_final_score_half(self):
        """Test calculating final score with half correct."""
        score = _calculate_final_score(5, 10)
        assert score == 50

    def test_calculate_final_score_zero(self):
        """Test calculating final score with no correct answers."""
        score = _calculate_final_score(0, 10)
        assert score == 0

    def test_calculate_final_score_partial(self):
        """Test calculating final score with partial correct answers."""
        score = _calculate_final_score(7, 10)
        assert score == 70

        score = _calculate_final_score(3, 4)
        assert score == 75

    def test_calculate_final_score_zero_questions(self):
        """Test calculating final score with zero questions."""
        score = _calculate_final_score(0, 0)
        assert score == 0

    def test_calculate_final_score_rounds_down(self):
        """Test that final score is rounded down to integer."""
        score = _calculate_final_score(1, 3)
        assert score == 33  # 33.333... rounds down to 33

# =============================================================================
# Test handle_grade_submission (Integration Tests)
# =============================================================================


@pytest.mark.asyncio
class TestHandleGradeSubmission:
    """Test suite for the handle_grade_submission async function."""

    async def test_handle_grade_submission_invalid_payload(self):
        """Test handling submission with invalid payload."""
        payload = {"invalid": "payload"}
        ctx = MagicMock(spec=WorkerContext)

        result = await handle_grade_submission(payload, ctx)

        assert result["status"] == "error"
        assert "Invalid payload" in result["message"]

    async def test_handle_grade_submission_missing_submission_id(self):
        """Test handling submission with missing submission_id."""
        payload = {"user_id": str(uuid.uuid4())}
        ctx = MagicMock(spec=WorkerContext)

        result = await handle_grade_submission(payload, ctx)

        assert result["status"] == "error"
        assert "Invalid payload" in result["message"]

    async def test_handle_grade_submission_quiz_not_found(
        self,
        test_db_manager,
        monkeypatch
    ):
        """Test handling submission when quiz attempt is not found."""
        submission_id = uuid.uuid4()
        user_id = uuid.uuid4()

        payload = {
            "submission_id": str(submission_id),
            "user_id": str(user_id)
        }

        ctx = WorkerContext(test_db_manager)

        result = await handle_grade_submission(payload, ctx)

        assert result["status"] == "error"
        assert "Quiz attempt not found" in result["message"]

    async def test_handle_grade_submission_no_answers(
        self,
        test_db: AsyncSession,
        test_db_manager,
        user_in_db
    ):
        """Test handling submission when quiz has no answers."""
        # Create a quiz attempt without answers
        quiz_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id="test-course",
            question_num=0,
            status=QuizStatus.IN_PROGRESS
        )
        test_db.add(quiz_attempt)
        await test_db.commit()
        await test_db.refresh(quiz_attempt)

        payload = {
            "submission_id": str(quiz_attempt.attempt_id),
            "user_id": str(user_in_db.id)
        }

        ctx = WorkerContext(test_db_manager)

        result = await handle_grade_submission(payload, ctx)

        assert result["status"] == "error"
        assert "Quiz attempt aborted" in result["message"]

        # Verify status was updated
        await test_db.refresh(quiz_attempt)
        assert quiz_attempt.status == QuizStatus.ABORTED

    async def test_handle_grade_submission_user_not_in_neo4j(
        self,
        test_db: AsyncSession,
        test_db_manager,
        user_in_db
    ):
        """Test handling submission when user is not found in Neo4j."""
        # TODO: Problem here
        # Create a quiz attempt with answers
        quiz_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id="test-course",
            question_num=1,
            status=QuizStatus.IN_PROGRESS
        )
        test_db.add(quiz_attempt)
        await test_db.commit()
        await test_db.refresh(quiz_attempt)

        # Add a submission answer
        answer = SubmissionAnswer(
            submission_id=quiz_attempt.attempt_id,
            question_id=uuid.uuid4(),
            user_answer={"user_answer": "A"}
        )
        test_db.add(answer)
        await test_db.commit()

        payload = {
            "submission_id": str(quiz_attempt.attempt_id),
            "user_id": str(user_in_db.id)
        }

        ctx = WorkerContext(test_db_manager)

        result = await handle_grade_submission(payload, ctx)

        assert result["status"] == "error"
        assert "User not found in graph" in result["message"]

    async def test_handle_grade_submission_success(
        self,
        test_db: AsyncSession,
        test_db_manager,
        course_in_db,
        user_in_neo4j_db,
        user_in_db,
        questions_in_neo4j_db,
        monkeypatch
    ):
        """Test successful grading of a submission."""
        mcq_question, fib_question = questions_in_neo4j_db
        course_one, _ = course_in_db

        # Create a quiz attempt
        quiz_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id=course_one.id,
            question_num=2,
            status=QuizStatus.IN_PROGRESS
        )
        test_db.add(quiz_attempt)
        await test_db.commit()
        await test_db.refresh(quiz_attempt)

        # Add submission answers (1 correct, 1 incorrect)
        answer1 = SubmissionAnswer(
            submission_id=quiz_attempt.attempt_id,
            question_id=UUID(str(mcq_question.question_id)),
            user_answer={"user_answer": "0"}  # Correct answer
        )
        answer2 = SubmissionAnswer(
            submission_id=quiz_attempt.attempt_id,
            question_id=UUID(str(fib_question.question_id)),
            user_answer={"user_answer": "wrong answer"}  # Incorrect answer
        )
        test_db.add(answer1)
        test_db.add(answer2)
        await test_db.commit()

        payload = {
            "submission_id": str(quiz_attempt.attempt_id),
            "user_id": str(user_in_db.id)
        }

        ctx = WorkerContext(test_db_manager)

        result = await handle_grade_submission(payload, ctx)

        assert result["status"] == "success"
        assert result["submission_id"] == str(quiz_attempt.attempt_id)
        assert result["total_questions"] == 2
        assert result["score"] == 50  # 1 out of 2 correct = 50%

        # Verify quiz attempt was updated
        await test_db.refresh(quiz_attempt)
        assert quiz_attempt.status == QuizStatus.COMPLETED
        assert quiz_attempt.score == 50
        assert quiz_attempt.submitted_at is not None

    async def test_handle_grade_submission_correct_answer_with_graph(
        self,
        test_db: AsyncSession,
        test_db_manager,
        course_in_db,
        user_in_neo4j_db,
        user_in_db,
        knowledge_graph_in_neo4j_db,
    ):
        """
        Test grading with correct answer in knowledge graph.

        Test Scenario:
        - Answer question for Subtopic A CORRECTLY
        - Should create mastery relationship
        - Should trigger upward propagation (if implemented)
        """
        graph = knowledge_graph_in_neo4j_db
        course_one, _ = course_in_db

        # Create a quiz attempt with one question
        quiz_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id=course_one.id,
            question_num=1,
            status=QuizStatus.IN_PROGRESS
        )
        test_db.add(quiz_attempt)
        await test_db.commit()
        await test_db.refresh(quiz_attempt)

        # Add CORRECT answer for Subtopic A
        answer_a = SubmissionAnswer(
            submission_id=quiz_attempt.attempt_id,
            question_id=UUID(str(graph['mcq_a'].question_id)),
            user_answer={"user_answer": "0"}  # Correct answer
        )
        test_db.add(answer_a)
        await test_db.commit()

        # Grade the submission
        payload = {
            "submission_id": str(quiz_attempt.attempt_id),
            "user_id": str(user_in_db.id)
        }

        ctx = WorkerContext(test_db_manager)
        result = await handle_grade_submission(payload, ctx)

        # Verify grading result
        assert result["status"] == "success"
        assert result["score"] == 100  # 1 correct out of 1 = 100%

        # Verify mastery relationship created
        async with test_db_manager.neo4j_scoped_connection():
            mastery_exists = await asyncio.to_thread(
                user_in_neo4j_db.mastery.is_connected,
                graph['subtopic_a']
            )
            assert mastery_exists, "Mastery should be created for correct answer"

        print("✅ Correct answer test passed: mastery created")

    async def test_handle_grade_submission_incorrect_answer_with_graph(
        self,
        test_db: AsyncSession,
        test_db_manager,
        course_in_db,
        user_in_neo4j_db,
        user_in_db,
        knowledge_graph_in_neo4j_db,
    ):
        """
        Test grading with incorrect answer in knowledge graph.

        Test Scenario:
        - Answer question for Subtopic B INCORRECTLY
        - Should still create mastery relationship (to track the attempt)
        - Should NOT propagate to prerequisites
        """
        graph = knowledge_graph_in_neo4j_db
        course_one, _ = course_in_db

        # Create a quiz attempt with one question
        quiz_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id=course_one.id,
            question_num=1,
            status=QuizStatus.IN_PROGRESS
        )
        test_db.add(quiz_attempt)
        await test_db.commit()
        await test_db.refresh(quiz_attempt)

        # Add INCORRECT answer for Subtopic B
        answer_b = SubmissionAnswer(
            submission_id=quiz_attempt.attempt_id,
            question_id=UUID(str(graph['mcq_b'].question_id)),
            user_answer={"user_answer": "0"}  # Wrong answer (correct is 1)
        )
        test_db.add(answer_b)
        await test_db.commit()

        # Grade the submission
        payload = {
            "submission_id": str(quiz_attempt.attempt_id),
            "user_id": str(user_in_db.id)
        }

        ctx = WorkerContext(test_db_manager)
        result = await handle_grade_submission(payload, ctx)

        # Verify grading result
        assert result["status"] == "success"
        assert result["score"] == 0  # 0 correct out of 1 = 0%

        # Verify mastery relationship created (even for wrong answer)
        async with test_db_manager.neo4j_scoped_connection():
            mastery_exists = await asyncio.to_thread(
                user_in_neo4j_db.mastery.is_connected,
                graph['subtopic_b']
            )
            assert mastery_exists, "Mastery should be created even for incorrect answer"

        print("✅ Incorrect answer test passed: mastery created but no propagation")
