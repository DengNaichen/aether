import uuid

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD, COURSE_ID, COURSE_NAME
from src.app.models.user import User
from src.app.models.course import Course


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_unauthenticated_user(
        client: AsyncClient,
        course_in_db: AsyncSession
):
    pass


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_already_enrolled(
        client: AsyncClient,
        course_in_db: AsyncSession
):
    pass


@pytest.mark.asyncio
async def test_enroll_a_course_failed_with_not_exist_course(
        client: AsyncClient,
        course_in_db: AsyncSession
):
    pass


@pytest.mark.asyncio
async def test_enroll_a_course_successful_as_authenticated_user(
        authenticated_client: AsyncClient,
        course_in_db: Course,
        user_in_db: User,
        test_db: AsyncSession
):
    # auth_headers = authenticated_client.headers

    enrollment_data = {
        "course_id": COURSE_ID
    }

    response = await authenticated_client.post("/enrollments/course",
                                 json=enrollment_data)

    assert response.status_code == 201

    await test_db.refresh(course_in_db)

    response_data = response.json()
    assert response_data["course_id"] == course_in_db.id

    await test_db.refresh(user_in_db)
    response_user_id = uuid.UUID(response_data["user_id"])
    assert response_user_id == user_in_db.id

    enrolled_user_from_db = await test_db.get(User, response_user_id)
    assert enrolled_user_from_db is not None
    assert enrolled_user_from_db.email == user_in_db.email
