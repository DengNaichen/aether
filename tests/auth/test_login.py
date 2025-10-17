import pytest
from asyncpg.pgproto.pgproto import timedelta
from httpx import AsyncClient

from src.app.core.security import create_access_token
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD

# TODO: 使用错误格式请求（例如少传username / password）
# TODO: 尝试用refresh_token登录（应失败）
# TODO: 锁定机制（如果有多次失败登录限制）


@pytest.mark.asyncio
async def test_login_success(
    client: AsyncClient,
    user_in_db: "User",  # TODO: how to fix the import problem, insert user into that our database
):
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    # if my api want the from_data(form data), I need to use data
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    result = response.json()

    assert "access_token" in result
    assert result["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_failed_with_nonexist(client: AsyncClient, user_in_db: "User"):
    login_data = {
        "username": "no_exist_student@example.com",
        "password": "invalid_password",
    }
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_failed_with_incorrect_password(
    client: AsyncClient, user_in_db: "User"
):
    login_data = {"username": TEST_USER_EMAIL, "password": "a-wrong-password123456"}
    response = await client.post("/auth/login", data=login_data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_protected_route_with_expired_token(
    client: AsyncClient, user_in_db: "User"
):
    login_data = {"username": "refresh@test.com", "password": "a-secure-password123456"}

    # create an expired token
    expired_token = create_access_token(user=login_data["username"],
                                        expires_delta=timedelta(minutes=-1))
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = await client.get("user/me", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_refresh_with_invalid_token(client: AsyncClient):
    refresh_payload = {"refresh_token": "this-is-not-a-valid-jwt"}
    response = await client.post("auth/refresh", json=refresh_payload)

    assert response.status_code == 401
    assert "Invalid refresh token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_with_expired_refresh_token(client: AsyncClient):
    expired_refresh_token = create_access_token(user="any@user.com",
                                                expires_delta=timedelta(
                                                    minutes=-1))
    refresh_payload = {"refresh_token": expired_refresh_token}
    response = await client.post("/auth/refresh", json=refresh_payload)

    assert response.status_code == 401
