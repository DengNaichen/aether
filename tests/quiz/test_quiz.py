from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app import Course

# Import the models to verify database state after API calls
from app import Quiz, QuizStatus, QuizSubmission
from app.models.user import User

# Import constants from your conftest to ensure consistency
from tests.conftest import COURSE_ID


@pytest.mark.asyncio
class TestStartNewQuiz:
    """
    Test suite for the POST /courses/{course_id}/quizzes endpoint.
    """

    async def test_start_quiz_success(
        self, enrolled_user_client: AsyncClient, test_db: AsyncSession, user_in_db: User
    ):
        """
        Tests the successful creation of a new dynamic quiz.
        - GIVEN: An authenticated user who is enrolled in an existing course.
        - WHEN: A POST request is made to start a quiz for that course.
        - THEN: The API should return a 201 CREATED status.
        - AND: The response body should match the QuizStartResponse schema.
        - AND: A new Quiz and QuizSubmission record should be created in the database.
        """
        payload = {"course_id": COURSE_ID, "question_num": 2}
        endpoint = f"/course/{COURSE_ID}/quizzes"

        # --- Make the API call ---
        response = await enrolled_user_client.post(endpoint, json=payload)

        # --- Assert the response ---
        assert (
            response.status_code == 201
        ), f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        assert "id" in data
        assert "submission_id" in data
        assert "questions" in data
        assert data["course_id"] == COURSE_ID
        assert data["question_num"] == payload["question_num"]
        # Assuming your mock_data function returns 2 questions
        assert len(data["questions"]) == 2

        # --- Assert the database state ---
        # Verify a Quiz was created
        quiz_query = await test_db.execute(
            select(Quiz).where(Quiz.id == UUID(data["id"]))
        )
        created_quiz = quiz_query.scalars().one_or_none()
        assert created_quiz is not None
        assert created_quiz.course_id == COURSE_ID

        # Verify a QuizSubmission was created and linked correctly
        submission_query = await test_db.execute(
            select(QuizSubmission).where(
                QuizSubmission.id == UUID(data["submission_id"])
            )
        )
        created_submission = submission_query.scalars().one_or_none()
        assert created_submission is not None
        assert created_submission.quiz_id == created_quiz.id
        assert created_submission.user_id == user_in_db.id
        assert created_submission.status == QuizStatus.IN_PROGRESS
        assert created_submission.score is None

    async def test_start_quiz_unauthenticated(self, client: AsyncClient):
        """
        Tests that an unauthenticated user cannot start a quiz.
        """
        payload = {"course_id": COURSE_ID, "question_num": 2}
        endpoint = f"/course/{COURSE_ID}/quizzes"
        response = await client.post(endpoint, json=payload)
        assert response.status_code == 401

    async def test_start_quiz_course_not_found(self, authenticated_client: AsyncClient):
        """
        Tests that starting a quiz for a non-existent course fails.
        """

        payload = {"course_id": COURSE_ID, "question_num": 2}
        non_existent_course_id = "course_that_does_not_exist"
        endpoint = f"/course/{non_existent_course_id}/quizzes"
        response = await authenticated_client.post(endpoint, json=payload)
        assert response.status_code == 404

    async def test_start_quiz_with_active_submission_conflict(
        self,
        enrolled_user_client: AsyncClient,
        test_db: AsyncSession,
        user_in_db: User,
        course_in_db: Course,
    ):
        """
        Tests that a user cannot start a new quiz if they already have one in progress
        for the same course.
        """
        # --- Manually create an "in-progress" submission for the user ---
        # 1. Create a quiz
        active_quiz = Quiz(course_id=course_in_db.id, question_num=10)
        test_db.add(active_quiz)
        await test_db.flush()  # Flush to get the ID

        # 2. Create a submission linked to the quiz and user
        active_submission = QuizSubmission(
            user_id=user_in_db.id, quiz_id=active_quiz.id, status=QuizStatus.IN_PROGRESS
        )
        test_db.add(active_submission)
        await test_db.commit()
        # --- End of setup ---

        # --- Attempt to start a new quiz ---
        payload = {"course_id": COURSE_ID, "question_num": 2}
        endpoint = f"/course/{COURSE_ID}/quizzes"
        response = await enrolled_user_client.post(endpoint, json=payload)

        # --- Assert the conflict ---
        assert response.status_code == 409
        assert "active quiz submission already exists" in response.json()["detail"]

    @pytest.mark.parametrize(
        "invalid_payload",
        [
            {},  # Missing question_num
            {"question_num": "five"},  # Wrong type for question_num
            {"question_num": -1},  # Invalid value
            {
                "question_num": 10,
                "extra": "field",
            },  # Extra field (though FastAPI often ignores this)
        ],
    )
    async def test_start_quiz_invalid_payload(
        self, enrolled_user_client: AsyncClient, invalid_payload: dict
    ):
        """
        Tests that the request fails with a validation error for invalid payloads.
        """
        endpoint = f"/course/{COURSE_ID}/quizzes"
        response = await enrolled_user_client.post(endpoint, json=invalid_payload)
        assert response.status_code == 422  # Unprocessable Entity
