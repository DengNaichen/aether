import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient
from fastapi import status

from src.app.models import Enrollment
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


@pytest.mark.asyncio
async def test_check_with_an_active_quiz():
    # "/quizzes/active"
    # 200
    pass


@pytest.mark.asyncio
async def test_check_with_no_active_quiz():
    # "/quizzes/active"
    # 404
    pass







@pytest.mark.asyncio
async def test_start_a_quiz_successfully_with_student_enrolled_course(
        enrolled_user_client: AsyncClient,
        enrollment_in_db: Enrollment,
):
    quiz_data = {
        "course_id": str(enrollment_in_db.id),
        "question_count": int(2),
    }
    response = await enrolled_user_client.post(
        "/quizzes/start",
        json=quiz_data,
    )

    assert response.status_code == status.HTTP_201_CREATED



@pytest.mark.asyncio
async def test_start_a_quiz_failed_without_student_enrolled_course(
        authenticated_client: AsyncClient,
        enrollment_in_db: Enrollment,
):
    pass
