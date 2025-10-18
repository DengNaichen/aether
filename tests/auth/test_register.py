import pytest
from httpx import AsyncClient
from starlette import status

from app.models.user import User
from tests.conftest import TEST_USER_EMAIL, TEST_USER_NAME, TEST_USER_PASSWORD


@pytest.mark.asyncio
async def test_register_failed_with_exsited_user(
        client: AsyncClient,
        user_in_db: User
):
    user_data = {
        "name": TEST_USER_NAME,
        "email": TEST_USER_EMAIL,
        "password": TEST_USER_PASSWORD,
    }
    response = await client.post("/users/register", json=user_data)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"detail": "Email already registered"}


@pytest.mark.asyncio
async def test_registration_success_with_empty_db(client: AsyncClient):
    # a successful registration student data
    new_student = {
        "name": "test user",
        "email": "test.user@example.com",
        "password": "a-secure-password123",
    }

    # send post-request
    response = await client.post("/users/register", json=new_student)
    # assert status code
    assert response.status_code == 201

    # assert return data
    response_data = response.json()
    assert "id" in response_data
    assert "created_at" in response_data
    assert isinstance(response_data["created_at"], str)
    # verify other fields
    assert response_data["name"] == new_student["name"]
    assert response_data["email"] == new_student["email"]
    # Ensure the password is not returned
    assert "password" not in response_data


@pytest.mark.parametrize(
    "syntactically_invalid_email",
    [
        "plainaddress",
        "#@%^%#$@#$@#.com",
        "@example.com",
        "email.example.com",
        "email@example@example.com",
        "email@example..com",
        "email@.example.com",
    ],
)
@pytest.mark.asyncio
async def test_registration_fails_for_syntactically_invalid_email_with_empty_db(
    client: AsyncClient, syntactically_invalid_email: str
):
    """
    for syntactically invalid email, API will return 422 error.
    """
    new_user_data = {
        "name": "Test Student",
        "email": syntactically_invalid_email,
        "password": "a-secure-password123",
    }

    response = await client.post("/users/register", json=new_user_data)

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["loc"] == ["body", "email"]


@pytest.mark.parametrize(
    "parseable_email",
    [
        "Joe Smith <email@example.com>",
        "test.email@example.com",
    ],
)
@pytest.mark.asyncio
async def test_registration_succeeds_for_parseable_email(
    parseable_email: str, client: AsyncClient
):
    """
    for parseable email, API will return 201 created.
    """
    new_user_data = {
        "name": "Another Student",
        "email": parseable_email,
        "password": "a-secure-password123",
    }

    response = await client.post("/users/register", json=new_user_data)

    assert response.status_code == 201


# TODO: test other field:
# TODO: password
# TODO: password too short
# TODO: password too long
# TODO: password complexity
# TODO: password is empty
# TODO: name
# TODO: null
# TODO: too long
# !@#$%^&*()

# TODO: Request body is incomplete
# TODO: email letter, upper case and lower case
