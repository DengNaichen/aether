import uuid
from fastapi import status
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.models import Enrollment
from tests.conftest import COURSE_ID
from src.app.models.user import User
from src.app.models.course import Course


# TODO: more test case here need for the enrollment

@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_unauthenticated_user(
        client: AsyncClient,
        course_in_db: Course,
):
    response = await client.post(
        f"/course/{course_in_db.id}/enrollments"
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()["detail"] == "Not authenticated"


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_not_exist_course(
        authenticated_client: AsyncClient
):
    non_existent_course_id = "not_exist"

    response = await authenticated_client.post(
        f"/course/{non_existent_course_id}/enrollments"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "Course not found"


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_already_enrolled(
        enrolled_user_client: AsyncClient,
        course_in_db: Course
):
    response = await enrolled_user_client.post(
        f"/course/{course_in_db.id}/enrollments"
    )
    # failed because already exist
    assert response.status_code == status.HTTP_409_CONFLICT
    assert response.json()["detail"] == "User already enrolled this course."


@pytest.mark.asyncio
async def test_enroll_a_course_successful_as_authenticated_user(
        authenticated_client: AsyncClient,
        course_in_db: Course,
        user_in_db: User,
        test_db: AsyncSession
):
    course_id = COURSE_ID
    response = await authenticated_client.post(
        f"/course/{course_id}/enrollments"
    )

    assert response.status_code == status.HTTP_201_CREATED

    enrollment_query = select(Enrollment).where(
        Enrollment.course_id == course_id,
        Enrollment.user_id == user_in_db.id
    )
    enrollment_from_db = (await test_db.execute(enrollment_query)).scalar_one_or_none()

    assert enrollment_from_db is not None, "Enrollment was not created"

    assert enrollment_from_db.course_id == course_in_db.id
    assert enrollment_from_db.user_id == user_in_db.id
