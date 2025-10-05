import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    """
    Test login success with correct credentials
    """
    new_student = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }
    register_response = await client.post("/register", json=new_student)
    assert register_response.status_code == 201

    login_data = {
        "email": new_student["email"],
        "password": new_student["password"]
    }
    response = await client.post("/login", json=login_data)
    assert response.status_code == 200
    result = response.json()

    assert "access_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failed_with_invalid_email(client):
    new_student = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }
    register_response = await client.post("/register", json=new_student)
    assert register_response.status_code == 201

    login_data = {
        "email": "invalid_email",
        "password": "invalid_password"
    }
    response = await client.post("/login", json=login_data)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_login_failed_with_no_exist(client):
    new_student = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }
    register_response = await client.post("/register", json=new_student)
    assert register_response.status_code == 201

    login_data = {
        "email": "no_exist_student@example.com",
        "password": "invalid_password"
    }
    response = await client.post("/login", json=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_failed_with_incorrect_password(client):
    new_student = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": ""
    }
    register_response = await client.post("/register", json=new_student)
    assert register_response.status_code == 201

    login_data = {
        "email": "test.student@example.com",
        "password": "invalid_password"
    }
    response = await client.post("/login", json=login_data)
    assert response.status_code == 401



