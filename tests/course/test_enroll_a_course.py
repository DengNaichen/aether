import uuid
from fastapi import status
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models import Enrollment
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD, COURSE_ID, COURSE_NAME
from src.app.models.user import User
from src.app.models.course import Course


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_unauthenticated_user(
        client: AsyncClient,
        course_in_db: Course,
        test_db: AsyncSession,
):
    enrollment_data = {
        "course_id": COURSE_ID,
    }
    response = await client.post(
        "/enrollments/course",
        json=enrollment_data,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # TODO: what else assert?


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_not_exist_course(
        authenticated_client: AsyncClient,
        course_in_db: Course,
        user_in_db: User,
        test_db: AsyncSession
):
    enrollment_data = {
        "course_id": "NOT_EXIST",
    }
    response = await authenticated_client.post(
        "/enrollments/course",
        json=enrollment_data
    )
    # the course do not exist in the database
    # TODO: not sure the status code
    assert response.status_code == status.HTTP_404_NOT_FOUND
    # TODO: what else assert need here ?


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_already_enrolled(
        enrolled_user_client: AsyncClient,
        course_in_db: AsyncSession,
        user_in_db: User,
        test_db: AsyncSession
):
    enrollment_data = {
        "course_id": COURSE_ID,
    }
    response = await enrolled_user_client.post(
        "/enrollments/course",
        json=enrollment_data
    )
    # failed because already exist(
    assert response.status_code == status.HTTP_400_BAD_REQUEST


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
