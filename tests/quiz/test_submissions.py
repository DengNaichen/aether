import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from src.app.models.user import User
from src.app.models.course import Course
from src.app.models.quiz import Quiz, QuizSubmission, SubmissionAnswer, QuizStatus

# TODO: turn off the ide

# --- Test Constants ---
# These UUIDs should match the ones in your mock_data for the start_quiz endpoint
QUESTION_1_ID = "11111111-1111-1111-1111-111111111111"
QUESTION_2_ID = "22222222-2222-2222-2222-222222222222"


# --- Fixtures ---

@pytest_asyncio.fixture(scope="function")
async def in_progress_submission(
    test_db: AsyncSession, user_in_db: User, course_in_db: Course
) -> QuizSubmission:
    """
    Creates a Quiz and an associated 'in-progress' QuizSubmission
    for the test user.
    """
    # 1. Create a parent Quiz
    new_quiz = Quiz(course_id=course_in_db.id, question_num=2)
    test_db.add(new_quiz)
    await test_db.flush()

    # 2. Create the submission record
    new_submission = QuizSubmission(
        user_id=user_in_db.id,
        quiz_id=new_quiz.id,
        status=QuizStatus.IN_PROGRESS,
    )
    test_db.add(new_submission)
    await test_db.commit()
    await test_db.refresh(new_submission)
    return new_submission


# --- Test Cases ---


@pytest.mark.asyncio
class TestSubmitQuizAnswers:
    """
    Test suite for the PATCH /submissions/{submission_id} endpoint.
    """

    async def test_submit_answers_success(
        self,
        enrolled_user_client: AsyncClient,
        test_db: AsyncSession,
        in_progress_submission: QuizSubmission,
    ):
        """
        Tests the successful submission of answers.
        """
        payload = {
            "score": 1,
            "answers": [
                {
                    "question_id": QUESTION_1_ID,
                    "user_answer": 0,
                    "is_correct": True,
                },
                {
                    "question_id": QUESTION_2_ID,
                    "user_answer": 1,
                    "is_correct": False,
                },
            ],
        }
        endpoint = f"/submissions/{in_progress_submission.id}"

        response = await enrolled_user_client.patch(endpoint, json=payload)

        # 1. Check response
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(in_progress_submission.id)
        assert data["status"] == "completed"
        assert data["score"] == 1
        assert data["submitted_at"] is not None
        assert len(data["answers"]) == 2
        assert data["answers"][0]["is_correct"] is True
        assert data["answers"][1]["is_correct"] is False

        # 2. Check database state for QuizSubmission
        db_submission = await test_db.get(QuizSubmission, in_progress_submission.id)
        assert db_submission.status == QuizStatus.COMPLETED
        assert db_submission.score == 1
        assert db_submission.submitted_at is not None

        # 3. Check database state for SubmissionAnswer
        answer_query = await test_db.execute(
            select(SubmissionAnswer).where(
                SubmissionAnswer.submission_id == in_progress_submission.id
            )
        )
        db_answers = answer_query.scalars().all()
        assert len(db_answers) == 2

    async def test_submit_to_nonexistent_submission(
        self, enrolled_user_client: AsyncClient
    ):
        """
        Tests submitting to a submission ID that does not exist.
        """
        non_existent_id = UUID("00000000-0000-0000-0000-000000000000")
        payload = {"score": 0, "answers": []}
        endpoint = f"/submissions/{non_existent_id}"
        response = await enrolled_user_client.patch(endpoint, json=payload)
        assert response.status_code == 404
        assert "Submission not found" in response.json()["detail"]

    async def test_submit_to_already_completed_submission(
        self,
        enrolled_user_client: AsyncClient,
        test_db: AsyncSession,
        in_progress_submission: QuizSubmission,
    ):
        """
        Tests attempting to submit an already completed quiz.
        """
        # Manually set the submission to COMPLETED
        in_progress_submission.status = QuizStatus.COMPLETED
        test_db.add(in_progress_submission)
        await test_db.commit()

        payload = {"score": 1, "answers": []}
        endpoint = f"/submissions/{in_progress_submission.id}"
        response = await enrolled_user_client.patch(endpoint, json=payload)
        assert response.status_code == 409
        assert "already completed" in response.json()["detail"]

    async def test_submit_to_another_users_submission(
        self,
        authenticated_client: AsyncClient, # A client that is NOT the owner
        test_db: AsyncSession,
        in_progress_submission: QuizSubmission,
    ):
        """
        Tests that a user cannot submit answers for another user's submission.
        NOTE: This test uses 'authenticated_client' which creates a different user
              than the one who owns 'in_progress_submission'.
        """
        # This client's user ID will not match in_progress_submission.user_id
        payload = {"score": 1, "answers": []}
        endpoint = f"/submissions/{in_progress_submission.id}"
        response = await authenticated_client.patch(endpoint, json=payload)
        assert response.status_code == 403
        assert "Not authorized" in response.json()["detail"]

    @pytest.mark.parametrize(
        "invalid_payload, expected_detail_part",
        [
            ({"answers": []}, "Field required"), # Missing score
            ({"score": 1}, "Field required"), # Missing answers
            ({"score": "one", "answers": []}, "Input should be a valid integer"), # Wrong type for score
            ({"score": 1, "answers": "not a list"}, "Input should be a valid list"), # Wrong type for answers
        ]
    )
    async def test_submit_with_invalid_payload(
        self,
        enrolled_user_client: AsyncClient,
        in_progress_submission: QuizSubmission,
        invalid_payload: dict,
        expected_detail_part: str
    ):
        """
        Tests submitting with various invalid payloads.
        """
        endpoint = f"/submissions/{in_progress_submission.id}"
        response = await enrolled_user_client.patch(endpoint, json=invalid_payload)
        assert response.status_code == 422
        assert expected_detail_part in str(response.json()["detail"])
