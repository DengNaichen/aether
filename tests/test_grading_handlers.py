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
    _grade_calculation,
    _grade_fill_in_blank,
    _grade_multiple_choice,
    _grade_single_answer,
    _update_mastery_level,
    _validate_grading_payload,
    grade_answer,
    handle_grade_submission,
)


# =============================================================================
# Test Helper Functions for Grading
# =============================================================================


@pytest.mark.asyncio
class TestGradingHelperFunctions:
    """Test suite for individual grading helper functions."""

    # --- Multiple Choice Tests ---

    def test_grade_multiple_choice_correct(self):
        """Test grading a correct multiple choice answer."""
        result = _grade_multiple_choice(0, 0)
        assert result is True

    def test_grade_multiple_choice_incorrect(self):
        """Test grading an incorrect multiple choice answer."""
        result = _grade_multiple_choice(0, 1)
        assert result is False

    def test_grade_multiple_choice_with_negative(self):
        """Test grading multiple choice with numeric answers."""
        result = _grade_multiple_choice(-1, -1)
        assert result is True

    # --- Fill in Blank Tests ---

    def test_grade_fill_in_blank_correct(self):
        """Test grading a correct fill-in-blank answer."""
        result = _grade_fill_in_blank("python", ["python", "Python"])
        assert result is True

    def test_grade_fill_in_blank_case_insensitive(self):
        """Test that fill-in-blank grading is case-insensitive."""
        result = _grade_fill_in_blank("PYTHON", ["python"])
        assert result is True

        result = _grade_fill_in_blank("PyThOn", ["python"])
        assert result is True

    def test_grade_fill_in_blank_whitespace_handling(self):
        """Test that fill-in-blank handles whitespace correctly."""
        result = _grade_fill_in_blank("  python  ", ["python"])
        assert result is True

    def test_grade_fill_in_blank_multiple_acceptable_answers(self):
        """Test fill-in-blank with multiple acceptable answers."""
        result = _grade_fill_in_blank("JS", ["JavaScript", "JS", "js"])
        assert result is True

        result = _grade_fill_in_blank("javascript", ["JavaScript", "JS"])
        assert result is True

    def test_grade_fill_in_blank_incorrect(self):
        """Test grading an incorrect fill-in-blank answer."""
        result = _grade_fill_in_blank("java", ["python", "Python"])
        assert result is False

    # --- Calculation Tests ---

    def test_grade_calculation_exact_match(self):
        """Test calculation grading with exact match."""
        result = _grade_calculation("3.14", "3.14", precision=2)
        assert result is True

    def test_grade_calculation_within_tolerance(self):
        """Test calculation grading within precision tolerance."""
        # precision=2 means tolerance of 0.01
        result = _grade_calculation("3.141", "3.14", precision=2)
        assert result is True

        result = _grade_calculation("3.145", "3.14", precision=2)
        assert result is True

    def test_grade_calculation_outside_tolerance(self):
        """Test calculation grading outside precision tolerance."""
        # precision=2 means tolerance of 0.01
        result = _grade_calculation("3.16", "3.14", precision=2)
        assert result is False

    def test_grade_calculation_different_precision_levels(self):
        """Test calculation grading with different precision levels."""
        # precision=0 means tolerance of 1
        result = _grade_calculation("100.5", "100", precision=0)
        assert result is True

        # precision=3 means tolerance of 0.001
        result = _grade_calculation("3.1415", "3.1414", precision=3)
        assert result is True

        result = _grade_calculation("3.1425", "3.1414", precision=3)
        assert result is False

    def test_grade_calculation_negative_numbers(self):
        """Test calculation grading with negative numbers."""
        result = _grade_calculation("-5.5", "-5.5", precision=1)
        assert result is True

        result = _grade_calculation("-5.55", "-5.5", precision=1)
        assert result is True

    def test_grade_calculation_invalid_input_raises_error(self):
        """Test that invalid input raises ValueError."""
        with pytest.raises(ValueError):
            _grade_calculation("not_a_number", "3.14", precision=2)

        with pytest.raises(ValueError):
            _grade_calculation("3.14", "invalid", precision=2)


# =============================================================================
# Test grade_answer Function
# =============================================================================


@pytest.mark.asyncio
class TestGradeAnswer:
    """Test suite for the main grade_answer function."""

    def test_grade_multiple_choice_question_correct(self):
        """Test grading a correct multiple choice question."""
        question_node = neo.MultipleChoice()
        question_node.question_id = str(uuid.uuid4())
        question_node.correct_answer = 2

        user_answer = {"user_answer": 2}

        result = grade_answer(question_node, user_answer)
        assert result is True

    def test_grade_multiple_choice_question_incorrect(self):
        """Test grading an incorrect type multiple choice question."""
        question_node = neo.MultipleChoice()
        question_node.question_id = str(uuid.uuid4())
        question_node.correct_answer = 1

        user_answer = {"user_answer": "1"}

        result = grade_answer(question_node, user_answer)
        assert result is False

    def test_grade_fill_in_blank_question_correct(self):
        """Test grading a correct fill-in-blank question."""
        question_node = neo.FillInBlank()
        question_node.question_id = str(uuid.uuid4())
        question_node.expected_answer = ["python", "Python"]

        user_answer = {"user_answer": "Python"}

        result = grade_answer(question_node, user_answer)
        assert result is True

    def test_grade_fill_in_blank_question_incorrect(self):
        """Test grading an incorrect fill-in-blank question."""
        question_node = neo.FillInBlank()
        question_node.question_id = str(uuid.uuid4())
        question_node.expected_answer = ["python"]

        user_answer = {"user_answer": "java"}

        result = grade_answer(question_node, user_answer)
        assert result is False

    def test_grade_calculation_question_correct(self):
        """Test grading a correct calculation question."""
        question_node = neo.Calculation()
        question_node.question_id = str(uuid.uuid4())
        question_node.expected_answer = ["3.14"]
        question_node.precision = 2

        user_answer = {"user_answer": "3.14"}

        result = grade_answer(question_node, user_answer)
        assert result is True

    def test_grade_calculation_question_incorrect(self):
        """Test grading an incorrect calculation question."""
        question_node = neo.Calculation()
        question_node.question_id = str(uuid.uuid4())
        question_node.expected_answer = ["3.14"]
        question_node.precision = 2

        user_answer = {"user_answer": "5.0"}

        result = grade_answer(question_node, user_answer)
        assert result is False

    def test_grade_answer_missing_user_answer(self):
        """Test that missing user_answer returns False."""
        question_node = neo.MultipleChoice()
        question_node.question_id = str(uuid.uuid4())
        question_node.correct_answer = 1

        # Empty dict
        result = grade_answer(question_node, {})
        assert result is False

        # None value
        result = grade_answer(question_node, {"user_answer": None})
        assert result is False

    def test_grade_answer_unknown_question_type(self):
        """Test that unknown question type returns False."""
        # Create a mock question node that's not one of the known types
        # Since Question is abstract, use MagicMock with the right base class
        from unittest.mock import MagicMock

        question_node = MagicMock(spec=neo.Question)
        question_node.question_id = str(uuid.uuid4())
        # Make isinstance checks fail for all known types
        question_node.__class__ = type('UnknownQuestion', (), {})

        user_answer = {"user_answer": "something"}

        result = grade_answer(question_node, user_answer)
        assert result is False

    def test_grade_answer_handles_exceptions(self):
        """Test that grade_answer handles exceptions gracefully."""
        question_node = neo.Calculation()
        question_node.question_id = str(uuid.uuid4())
        question_node.expected_answer = ["3.14"]
        question_node.precision = 2

        # Invalid numeric input
        user_answer = {"user_answer": "not_a_number"}
        result = grade_answer(question_node, user_answer)
        assert result is False


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

    def test_update_mastery_level_creates_new_relationship(self):
        """Test that _update_mastery_level creates a new relationship."""
        # Create mock objects
        neo_user = MagicMock(spec=neo.User)
        knode = MagicMock(spec=neo.KnowledgeNode)

        # Mock that no relationship exists
        neo_user.mastery.relationship.return_value = None

        # Mock the connect method to return a new relationship
        new_rel = MagicMock()
        neo_user.mastery.connect.return_value = new_rel

        # Call the function
        _update_mastery_level(neo_user, knode, True, "test-user-id")

        # Verify connect was called
        neo_user.mastery.connect.assert_called_once_with(knode)

        # Verify score was set correctly for correct answer
        assert new_rel.score == 0.9
        assert new_rel.last_update is not None
        new_rel.save.assert_called_once()

    def test_update_mastery_level_updates_existing_relationship_correct(self):
        """Test updating existing relationship with correct answer."""
        neo_user = MagicMock(spec=neo.User)
        knode = MagicMock(spec=neo.KnowledgeNode)

        # Mock an existing relationship
        existing_rel = MagicMock()
        neo_user.mastery.relationship.return_value = existing_rel

        # Call with correct answer
        _update_mastery_level(neo_user, knode, True, "test-user-id")

        # Verify score was set for correct answer
        assert existing_rel.score == 0.9
        assert existing_rel.last_update is not None
        existing_rel.save.assert_called_once()

    def test_update_mastery_level_updates_existing_relationship_incorrect(self):
        """Test updating existing relationship with incorrect answer."""
        neo_user = MagicMock(spec=neo.User)
        knode = MagicMock(spec=neo.KnowledgeNode)

        # Mock an existing relationship
        existing_rel = MagicMock()
        neo_user.mastery.relationship.return_value = existing_rel

        # Call with incorrect answer
        _update_mastery_level(neo_user, knode, False, "test-user-id")

        # Verify score was set for incorrect answer
        assert existing_rel.score == 0.2
        assert existing_rel.last_update is not None
        existing_rel.save.assert_called_once()


# =============================================================================
# Test _grade_single_answer
# =============================================================================


@pytest.mark.asyncio
class TestGradeSingleAnswer:
    """Test suite for _grade_single_answer function."""

    def test_grade_single_answer_correct(self, monkeypatch):
        """Test grading a single correct answer."""
        # Create mock answer
        answer = MagicMock(spec=SubmissionAnswer)
        answer.question_id = uuid.uuid4()
        answer.user_answer = {"user_answer": "A"}

        # Create mock question node
        question_node = MagicMock(spec=neo.MultipleChoice)
        question_node.question_id = str(answer.question_id)
        question_node.correct_answer = "A"

        # Create mock knowledge node
        knode = MagicMock(spec=neo.KnowledgeNode)
        question_node.knowledge_node.get.return_value = knode

        # Create a mock nodes manager with get_or_none method
        mock_nodes_manager = MagicMock()
        mock_nodes_manager.get_or_none.return_value = question_node

        # Mock neo.Question.nodes
        monkeypatch.setattr(neo.Question, "nodes", mock_nodes_manager)

        # Create mock user
        neo_user = MagicMock(spec=neo.User)
        neo_user.mastery.relationship.return_value = None
        new_rel = MagicMock()
        neo_user.mastery.connect.return_value = new_rel

        # Mock grade_answer to return True
        def mock_grade_answer(q_node, user_ans):
            return True

        import app.worker.handlers
        monkeypatch.setattr(app.worker.handlers, "grade_answer", mock_grade_answer)

        # Call the function
        result = _grade_single_answer(answer, neo_user, "test-user-id")

        # Verify result
        assert result is True
        assert answer.is_correct is True

    def test_grade_single_answer_question_not_found(self, monkeypatch):
        """Test grading when question is not found in Neo4j."""
        # Create mock answer
        answer = MagicMock(spec=SubmissionAnswer)
        answer.question_id = uuid.uuid4()
        answer.user_answer = {"user_answer": "A"}

        # Create a mock nodes manager that returns None
        mock_nodes_manager = MagicMock()
        mock_nodes_manager.get_or_none.return_value = None

        # Mock neo.Question.nodes
        monkeypatch.setattr(neo.Question, "nodes", mock_nodes_manager)

        # Create mock user
        neo_user = MagicMock(spec=neo.User)

        # Call the function
        result = _grade_single_answer(answer, neo_user, "test-user-id")

        # Verify result
        assert result is False
        assert answer.is_correct is False

    def test_grade_single_answer_no_knowledge_node(self, monkeypatch):
        """Test grading when question has no associated knowledge node."""
        # Create mock answer
        answer = MagicMock(spec=SubmissionAnswer)
        answer.question_id = uuid.uuid4()
        answer.user_answer = {"user_answer": "A"}

        # Create mock question node without knowledge node
        question_node = MagicMock(spec=neo.MultipleChoice)
        question_node.question_id = str(answer.question_id)
        question_node.knowledge_node.get.return_value = None

        # Create a mock nodes manager
        mock_nodes_manager = MagicMock()
        mock_nodes_manager.get_or_none.return_value = question_node

        # Mock neo.Question.nodes
        monkeypatch.setattr(neo.Question, "nodes", mock_nodes_manager)

        # Create mock user
        neo_user = MagicMock(spec=neo.User)

        # Mock grade_answer to return True
        def mock_grade_answer(q_node, user_ans):
            return True

        import app.worker.handlers
        monkeypatch.setattr(app.worker.handlers, "grade_answer", mock_grade_answer)

        # Call the function
        result = _grade_single_answer(answer, neo_user, "test-user-id")

        # Verify result - should still grade correctly but not update mastery
        assert result is True
        assert answer.is_correct is True


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
        user_in_neo4j_db,
        user_in_db,
        questions_in_neo4j_db,
        monkeypatch
    ):
        """Test successful grading of a submission."""
        mcq_question, fib_question = questions_in_neo4j_db

        # Create a quiz attempt
        quiz_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id="test-course",
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
