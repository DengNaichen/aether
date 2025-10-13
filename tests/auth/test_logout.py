import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import TEST_USER_PASSWORD, TEST_USER_EMAIL

# TODO: 测试使用已登出的令牌再次登出 (应失败)
# TODO: 检查令牌是否真的被加入了黑名单或失效列表 (如果后端实现了该机制)


@pytest.mark.asyncio
async def test_logout_success(
        client: AsyncClient,
        user_in_db: "User",
        test_db: AsyncSession,
):
    """
    测试成功登出。
    1. 先登录以获取有效的 access_token。
    2. 使用该 token 调用登出接口。
    3. 断言响应状态码为 200，并检查返回的消息。
    """
    # 步骤 1: 登录获取 token
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 步骤 2: 调用登出接口
    logout_response = await client.post("/auth/logout", headers=headers)

    # 步骤 3: 断言登出成功
    assert logout_response.status_code == 200
    # 假设成功登出后返回此消息，请根据您的实际 API 进行调整
    assert logout_response.json() == {"message": "Successfully logged out"}


@pytest.mark.asyncio
async def test_access_protected_route_after_logout(
    client: AsyncClient,
    user_in_db: "User"
):
    """
    测试登出后，refresh_token 是否失效。
    1. 登录获取 access_token 和 refresh_token。
    2. 执行登出操作。
    3. 使用同一个 refresh_token 尝试刷新。
    4. 断言刷新被拒绝 (401 Unauthorized)。
    """
    # 步骤 1: 登录
    login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
    login_response = await client.post("/auth/login", data=login_data)
    assert login_response.status_code == 200
    tokens = login_response.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    headers = {"Authorization": f"Bearer {access_token}"}

    # 步骤 2: 登出
    logout_response = await client.post("/auth/logout", headers=headers)
    assert logout_response.status_code == 200

    # 步骤 3: 使用已登出的 refresh_token 尝试刷新
    refresh_data = {"refresh_token": refresh_token}
    refresh_response = await client.post("/auth/refresh", json=refresh_data)

    # 步骤 4: 断言刷新失败
    assert refresh_response.status_code == 401
    # 这个错误信息取决于你的 refresh 接口在数据库找不到匹配的 refresh_token 时的返回
    assert refresh_response.json()["detail"] == "Invalid refresh token"


@pytest.mark.asyncio
async def test_logout_with_invalid_token(client: AsyncClient):
    """
    测试使用一个无效的 token 尝试登出。
    """
    headers = {"Authorization": "Bearer this-is-an-invalid-token"}
    response = await client.post("/auth/logout", headers=headers)

    assert response.status_code == 401
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.asyncio
async def test_logout_without_token(client: AsyncClient):
    """
    测试在未提供 token 的情况下请求登出接口。
    """
    response = await client.post("/auth/logout")

    # FastAPI 在缺少 Authorization header 时通常会返回 401
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"