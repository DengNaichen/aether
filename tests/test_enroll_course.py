import uuid

import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD
from src.app.models.user import User


@pytest.mark.asyncio
async def test_enroll_a_course_as_authenticated_user(client: AsyncClient,
                                                     test_db: AsyncSession):
    # login for the token
    login_data = {
        "username": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD
    }
    login_response = await client.post('auth/login', data=login_data)
    assert login_response.status_code == 200
    access_token = login_response.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # then try to enroll a course
    enrollment_data = {
        "course_id": "g11_phys"
    }

    response = await client.post("/enrollments/course",
                                 json=enrollment_data,
                                 headers=auth_headers)

    assert response.status_code == 201
    response_data = response.json()
    assert response_data["course_id"] == "g11_phys"

    user_id_str = response_data["student_id"]
    user_id_uuid = uuid.UUID(user_id_str)

    user_in_db = await test_db.get(User, user_id_uuid)

    assert user_in_db is not None
    assert user_in_db.email == TEST_USER_EMAIL
