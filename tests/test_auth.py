import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """
    Test login success with correct credentials
    """
    new_user = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }
    register_response = await client.post("/user/register", json=new_user)
    assert register_response.status_code == 201

    login_data = {
        "username": new_user["email"],
        "password": new_user["password"]
    }
    # if my api want the from_data(form data), I need to use data
    response = await client.post("/auth/auth", data=login_data)
    assert response.status_code == 200
    result = response.json()

    assert "access_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failed_with_nonexist(client):
    new_user = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }
    register_response = await client.post("/user/register", json=new_user)
    assert register_response.status_code == 201

    login_data = {
        "username": "no_exist_student@example.com",
        "password": "invalid_password"
    }
    response = await client.post("/auth/auth", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_failed_with_incorrect_password(client):
    new_user = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": ""
    }
    register_response = await client.post("user/register", json=new_user)
    assert register_response.status_code == 201

    login_data = {
        "username": "test.student@example.com",
        "password": "invalid_password"
    }
    response = await client.post("/auth/auth", data=login_data)
    assert response.status_code == 401

