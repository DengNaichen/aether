from uuid import UUID
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException

from app.models.course import Course
from app.models.quiz import QuizStatus, QuizAttempt
from app.models.user import User
from tests.conftest import COURSE_ID_ONE

# Import the helper functions we want to test
from app.routes.quiz import (
    _build_question_dict,
    _check_existing_quiz_attempt,
    _create_quiz_attempt,
    get_validated_course_for_user,
    get_random_question_for_user,
    UserNotFoundInNeo4j,
    CourseNotFoundOrNotEnrolledInNeo4j,
    NoQuestionFoundInNeo4j,
)


@pytest.mark.asyncio
class TestStartNewQuiz:
    """
    Test suite for the POST /courses/{course_id}/quizzes endpoint.
    """
    async def test_start_quiz_happy_path_with_real_question(
            self,
            enrolled_user_client: AsyncClient,
            test_db: AsyncSession,
            user_in_db: User,
            course_in_db: Course,
            # neo4j fixtures
            course_in_neo4j_db,
            user_in_neo4j_db,
            questions_in_neo4j_db,
    ):
        """
        Happy path test for starting a quiz, fetching a real question from Neo4j.
        """
        payload = {"question_num": 1}
        url = f"/course/{COURSE_ID_ONE}/quizzes"

        # --- Make the API call ---
        response = await enrolled_user_client.post(url, json=payload)

        # --- Assert the response ---
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        assert "attempt_id" in data
        assert "questions" in data
        assert data["course_id"] == COURSE_ID_ONE
        assert data["question_num"] == payload["question_num"]
        assert len(data["questions"]) == 1  # We requested one random question

        # --- Assert question structure ---
        question = data["questions"][0]
        assert "question_id" in question
        assert "text" in question
        assert "difficulty" in question
        assert "question_type" in question
        assert "details" in question

        # --- Assert database state ---
        submission_query = await test_db.execute(
            select(QuizAttempt).where(
                QuizAttempt.attempt_id == UUID(data["attempt_id"])
            )
        )
        created_submission = submission_query.scalars().one_or_none()
        assert created_submission is not None
        assert created_submission.user_id == user_in_db.id
        assert created_submission.status == QuizStatus.IN_PROGRESS
        assert created_submission.course_id == COURSE_ID_ONE


class TestBuildQuestionDict:
    """
    Unit tests for the _build_question_dict helper function.
    """

    def test_build_multiple_choice_question(self):
        """Test building a multiple choice question dictionary."""
        flat_props = {
            "question_id": "11111111-1111-1111-1111-111111111111",
            "text": "What is 2+2?",
            "difficulty": "easy",
            "options": ["3", "4", "5"],
            "correct_answer": 1,
        }
        kn_id = "test_node_123"
        labels = ["MultipleChoice", "Question"]

        result = _build_question_dict(flat_props, kn_id, labels)

        assert result["question_id"] == flat_props["question_id"]
        assert result["text"] == flat_props["text"]
        assert result["difficulty"] == flat_props["difficulty"]
        assert result["knowledge_node_id"] == kn_id
        assert result["question_type"] == "multiple_choice"
        assert result["details"]["question_type"] == "multiple_choice"
        assert result["details"]["options"] == flat_props["options"]
        assert result["details"]["correct_answer"] == flat_props["correct_answer"]

    def test_build_fill_in_blank_question(self):
        """Test building a fill in the blank question dictionary."""
        flat_props = {
            "question_id": "22222222-2222-2222-2222-222222222222",
            "text": "The capital of France is ____.",
            "difficulty": "medium",
            "expected_answer": ["Paris", "paris"],
        }
        kn_id = "test_node_456"
        labels = ["FillInBlank", "Question"]

        result = _build_question_dict(flat_props, kn_id, labels)

        assert result["question_id"] == flat_props["question_id"]
        assert result["text"] == flat_props["text"]
        assert result["difficulty"] == flat_props["difficulty"]
        assert result["knowledge_node_id"] == kn_id
        assert result["question_type"] == "fill_in_the_blank"
        assert result["details"]["question_type"] == "fill_in_the_blank"
        assert result["details"]["expected_answer"] == flat_props["expected_answer"]

    def test_build_calculation_question(self):
        """Test building a calculation question dictionary."""
        flat_props = {
            "question_id": "33333333-3333-3333-3333-333333333333",
            "text": "Calculate the area of a circle with radius 5.",
            "difficulty": "hard",
            "expected_answer": ["78.54"],
            "precision": 2,
        }
        kn_id = "test_node_789"
        labels = ["Calculation", "Question"]

        result = _build_question_dict(flat_props, kn_id, labels)

        assert result["question_id"] == flat_props["question_id"]
        assert result["text"] == flat_props["text"]
        assert result["difficulty"] == flat_props["difficulty"]
        assert result["knowledge_node_id"] == kn_id
        assert result["question_type"] == "calculation"
        assert result["details"]["question_type"] == "calculation"
        assert result["details"]["expected_answer"] == flat_props["expected_answer"]
        assert result["details"]["precision"] == 2

    def test_build_calculation_question_default_precision(self):
        """Test calculation question uses default precision if not provided."""
        flat_props = {
            "question_id": "44444444-4444-4444-4444-444444444444",
            "text": "Calculate something.",
            "difficulty": "easy",
            "expected_answer": ["10"],
        }
        kn_id = "test_node_xyz"
        labels = ["Calculation", "Question"]

        result = _build_question_dict(flat_props, kn_id, labels)

        assert result["details"]["precision"] == 2

    def test_build_question_unknown_type_raises_error(self):
        """Test that unknown question type raises ValueError."""
        flat_props = {
            "question_id": "55555555-5555-5555-5555-555555555555",
            "text": "Some question",
            "difficulty": "medium",
        }
        kn_id = "test_node_abc"
        labels = ["UnknownType", "Question"]

        with pytest.raises(ValueError) as exc_info:
            _build_question_dict(flat_props, kn_id, labels)

        assert "Unknown Neo4j question type" in str(exc_info.value)
        assert "UnknownType" in str(exc_info.value)


@pytest.mark.asyncio
class TestCheckExistingQuizAttempt:
    """
    Unit tests for the _check_existing_quiz_attempt helper function.
    """

    async def test_no_existing_attempt_passes(
        self,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test that function passes when no existing attempt exists."""
        # Should not raise any exception
        await _check_existing_quiz_attempt(
            test_db,
            user_in_db.id,
            COURSE_ID_ONE
        )

    async def test_existing_completed_attempt_passes(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course,
    ):
        """Test that completed attempts don't block new attempts."""
        course_one, _ = course_in_db

        # Create a completed quiz attempt
        completed_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id=course_one.id,
            question_num=1,
            status=QuizStatus.COMPLETED,
        )
        test_db.add(completed_attempt)
        await test_db.commit()

        # Should not raise any exception
        await _check_existing_quiz_attempt(
            test_db,
            user_in_db.id,
            course_one.id
        )

    async def test_existing_in_progress_attempt_raises_conflict(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course,
    ):
        """Test that in-progress attempt raises HTTP 409 Conflict."""
        course_one, _ = course_in_db

        # Create an in-progress quiz attempt
        in_progress_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id=course_one.id,
            question_num=1,
            status=QuizStatus.IN_PROGRESS,
        )
        test_db.add(in_progress_attempt)
        await test_db.commit()

        # Should raise HTTPException with 409 status
        with pytest.raises(HTTPException) as exc_info:
            await _check_existing_quiz_attempt(
                test_db,
                user_in_db.id,
                course_one.id
            )

        assert exc_info.value.status_code == 409
        assert "active quiz attempt already exists" in exc_info.value.detail.lower()

    async def test_different_course_does_not_block(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course,
    ):
        """Test that in-progress attempt for different course doesn't block."""
        course_one, course_two = course_in_db

        # Create an in-progress quiz attempt for course_one
        in_progress_attempt = QuizAttempt(
            user_id=user_in_db.id,
            course_id=course_one.id,
            question_num=1,
            status=QuizStatus.IN_PROGRESS,
        )
        test_db.add(in_progress_attempt)
        await test_db.commit()

        # Should not raise exception for course_two
        await _check_existing_quiz_attempt(
            test_db,
            user_in_db.id,
            course_two.id
        )


@pytest.mark.asyncio
class TestCreateQuizAttempt:
    """
    Unit tests for the _create_quiz_attempt helper function.
    """

    async def test_create_quiz_attempt_success(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course,
    ):
        """Test successfully creating a quiz attempt."""
        course_one, _ = course_in_db
        question_num = 5

        result = await _create_quiz_attempt(
            test_db,
            user_in_db.id,
            course_one.id,
            question_num
        )

        assert result is not None
        assert isinstance(result, QuizAttempt)
        assert result.user_id == user_in_db.id
        assert result.course_id == course_one.id
        assert result.question_num == question_num
        assert result.status == QuizStatus.IN_PROGRESS
        assert result.attempt_id is not None
        assert result.created_at is not None

    async def test_created_attempt_persisted_in_db(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course,
    ):
        """Test that created attempt is actually saved to database."""
        course_one, _ = course_in_db
        question_num = 3

        created_attempt = await _create_quiz_attempt(
            test_db,
            user_in_db.id,
            course_one.id,
            question_num
        )

        # Query database to verify it was persisted
        query = select(QuizAttempt).where(
            QuizAttempt.attempt_id == created_attempt.attempt_id
        )
        result = await test_db.execute(query)
        db_attempt = result.scalars().one_or_none()

        assert db_attempt is not None
        assert db_attempt.attempt_id == created_attempt.attempt_id
        assert db_attempt.user_id == user_in_db.id
        assert db_attempt.course_id == course_one.id


@pytest.mark.asyncio
class TestGetValidatedCourseForUser:
    """
    Unit tests for the get_validated_course_for_user function.
    """

    async def test_valid_user_and_enrollment(
        self,
        neo4j_test_driver,
        course_in_neo4j_db,
        user_in_neo4j_db,
        user_in_db: User,
    ):
        """Test successful validation when user is enrolled in course."""
        result = await get_validated_course_for_user(
            neo4j_test_driver,
            str(user_in_db.id),
            COURSE_ID_ONE
        )

        assert result is not None
        assert isinstance(result, dict)
        assert "course_id" in result or result  # Neo4j returns course properties

    async def test_user_not_found_raises_exception(
        self,
        neo4j_test_driver,
        course_in_neo4j_db,
    ):
        """Test that non-existent user raises UserNotFoundInNeo4j."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"

        with pytest.raises(UserNotFoundInNeo4j) as exc_info:
            await get_validated_course_for_user(
                neo4j_test_driver,
                fake_user_id,
                COURSE_ID_ONE
            )

        assert fake_user_id in str(exc_info.value)

    async def test_user_not_enrolled_raises_exception(
        self,
        neo4j_test_driver,
        course_in_neo4j_db,
        user_in_neo4j_db,
        user_in_db: User,
    ):
        """Test that non-enrolled course raises CourseNotFoundOrNotEnrolledInNeo4j."""
        fake_course_id = "non_existent_course"

        with pytest.raises(CourseNotFoundOrNotEnrolledInNeo4j) as exc_info:
            await get_validated_course_for_user(
                neo4j_test_driver,
                str(user_in_db.id),
                fake_course_id
            )

        assert fake_course_id in str(exc_info.value)
        assert str(user_in_db.id) in str(exc_info.value)


@pytest.mark.asyncio
class TestGetRandomQuestionForUser:
    """
    Unit tests for the get_random_question_for_user function.
    """

    async def test_get_random_question_success(
        self,
        neo4j_test_driver,
        course_in_neo4j_db,
        user_in_neo4j_db,
        user_in_db: User,
        questions_in_neo4j_db,
    ):
        """Test successfully fetching a random question."""
        result = await get_random_question_for_user(
            neo4j_test_driver,
            str(user_in_db.id),
            COURSE_ID_ONE
        )

        assert result is not None
        assert isinstance(result, dict)
        assert "question_id" in result
        assert "text" in result
        assert "difficulty" in result
        assert "knowledge_node_id" in result
        assert "question_type" in result
        assert "details" in result

    async def test_question_type_is_valid(
        self,
        neo4j_test_driver,
        course_in_neo4j_db,
        user_in_neo4j_db,
        user_in_db: User,
        questions_in_neo4j_db,
    ):
        """Test that returned question has a valid type."""
        result = await get_random_question_for_user(
            neo4j_test_driver,
            str(user_in_db.id),
            COURSE_ID_ONE
        )

        valid_types = ["multiple_choice", "fill_in_the_blank", "calculation"]
        assert result["question_type"] in valid_types

    async def test_no_questions_raises_exception(
        self,
        neo4j_test_driver,
        course_in_neo4j_db,
        user_in_neo4j_db,
        user_in_db: User,
    ):
        """Test that course without questions raises NoQuestionFoundInNeo4j."""
        # No questions_in_neo4j_db fixture, so no questions exist

        with pytest.raises(NoQuestionFoundInNeo4j) as exc_info:
            await get_random_question_for_user(
                neo4j_test_driver,
                str(user_in_db.id),
                COURSE_ID_ONE
            )

        assert COURSE_ID_ONE in str(exc_info.value)
