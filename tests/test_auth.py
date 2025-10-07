import pytest
from asyncpg.pgproto.pgproto import timedelta
from httpx import AsyncClient

from app.core.security import create_access_token

# TODO: 使用错误格式请求（例如少传username / password）
# TODO: 尝试用refresh_token登录（应失败）
# TODO: 锁定机制（如果有多次失败登录限制）


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
    register_response = await client.post("/auth/register", json=new_user)
    assert register_response.status_code == 201

    login_data = {
        "username": new_user["email"],
        "password": new_user["password"]
    }
    # if my api want the from_data(form data), I need to use data
    response = await client.post("/auth/login", data=login_data)
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
    register_response = await client.post("/auth/register", json=new_user)
    assert register_response.status_code == 201

    login_data = {
        "username": "no_exist_student@example.com",
        "password": "invalid_password"
    }
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_failed_with_incorrect_password(client):
    new_user = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": "a-secure-password123"
    }
    register_response = await client.post("auth/register", json=new_user)
    assert register_response.status_code == 201

    login_data = {
        "username": "test.student@example.com",
        "password": "a-secure-password123456"
    }
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_protected_route_with_expired_token(client: AsyncClient):
    new_user = {
        "name": "Test Student",
        "email": "test.student@example.com",
        "password": ""
    }
    register_response = await client.post("auth/register", json=new_user)
    assert register_response.status_code == 201

    # create an expired token
    expired_token = create_access_token(
        subject=new_user["email"],
        expires_delta=timedelta(minutes=-1)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("user/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_successful_token_refresh(client: AsyncClient):
    new_user = {
        "name": "Test Student",
        "email": "refresh@test.com",
        "password": "a-secure-password123456"
    }
    await client.post("/auth/register", json=new_user)

    login_data = {
        "username": "refresh@test.com",
        "password": "a-secure-password123456"
    }
    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200

    tokens = login_response.json()
    initial_access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    refresh_payload = {"refresh_token": refresh_token}
    refresh_response = await client.post("/auth/refresh",
                                         json=refresh_payload)

    assert refresh_response.status_code == 200
    new_tokens = refresh_response.json()
    assert "access_token" in new_tokens
    assert new_tokens["token_type"] == "bearer"

    assert new_tokens["access_token"] != initial_access_token


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    refresh_payload = {"refresh_token": "this-is-not-a-valid-jwt"}
    response = await client.post("auth/refresh", json=refresh_payload)

    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_with_expired_refresh_token(client: AsyncClient):
    expired_refresh_token = create_access_token(
        subject="any@user.com",
        expires_delta=timedelta(minutes=-1)
    )
    refresh_payload = {"refresh_token": expired_refresh_token}
    response = await client.post("/auth/refresh", json=refresh_payload)

    assert response.status_code == 401
