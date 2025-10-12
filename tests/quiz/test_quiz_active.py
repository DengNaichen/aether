# import pytest
# from sqlalchemy.ext.asyncio import AsyncSession
# from httpx import AsyncClient
#
# from conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD
#
# @pytest.mark.asyncio
# async def test_quiz_active_session(client: AsyncClient,
#                                     test_db: AsyncSession):
#     pass
    # First, login and enroll the user in a course
    # login_data = {
    #     "username": TEST_USER_EMAIL,
    #     "password": TEST_USER_PASSWORD
    # }
    # login_response = await client.post('auth/login', data=login_data)
    # assert login_response.status_code == 200
    # access_token = login_response.json()["access_token"]
    # auth_headers = {"Authorization": f"Bearer {access_token}"}
    # enrollment_data = {
    #     "course_id": "g11_phys"
    # }
    # enroll_response = await client.post("/enrollments/course",
    #                                     json=enrollment_data,
    #                                     headers=auth_headers)
    # assert enroll_response.status_code == 201
    # response_data = enroll_response.json()
    # assert response_data["course_id"] == "g11_phys"