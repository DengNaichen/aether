import pytest


@pytest.mark.asyncio
async def test_registration_success(client):
    # a successful registration student data
    new_student = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }

    # send post-request
    response = await client.post("/user/register",
                                 json=new_student)
    # assert status code
    assert response.status_code == 201
    # assert return data
    response_data = response.json()

    # verify id
    assert "id" in response_data

    # verify create at
    assert "created_at" in response_data
    # verify it is not None and is a string
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
async def test_registration_fails_for_syntactically_invalid_email(
    syntactically_invalid_email: str, client
):
    """
    for syntactically invalid email, API will return 422 error.
    """
    new_user_data = {
        "name": "Test Student",
        "email": syntactically_invalid_email,
        "password": "a-secure-password123",
    }

    response = await client.post("/user/register", json=new_user_data)

    assert response.status_code == 422
    response_data = response.json()
    assert response_data["detail"][0]["loc"] == ["body", "email"]


@pytest.mark.parametrize(
    "parseable_email",
    [
        "Joe Smith <email@example.com>",
        "test.email@example.com",
    ]
)
@pytest.mark.asyncio
async def test_registration_succeeds_for_parseable_email(parseable_email: str,
                                                         client):
    """
    for parseable email, API will return 201 created.
    """
    new_user_data = {
        "name": "Another Student",
        "email": parseable_email,
        "password": "a-secure-password123",
    }

    response = await client.post("/user/register", json=new_user_data)

    assert response.status_code == 201
