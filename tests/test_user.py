import pytest
from asyncpg.pgproto.pgproto import timedelta
from httpx import AsyncClient

from app.core.security import create_access_token
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD
import pytest
from httpx import AsyncClient
from starlette import status

from app.models.user import User
from tests.conftest import TEST_USER_EMAIL, TEST_USER_NAME, TEST_USER_PASSWORD
from sqlalchemy.ext.asyncio import AsyncSession

# TODO: 使用错误格式请求（例如少传username / password）
# TODO: 尝试用refresh_token登录（应失败）
# TODO: 锁定机制（如果有多次失败登录限制）


class TestRegister:
    @pytest.mark.asyncio
    async def test_register_failed_with_exsited_user(
            self,
            client: AsyncClient,
            user_in_db: "User"
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
    async def test_registration_success_with_empty_db(
            self,
            client: AsyncClient
    ):
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
            self, client: AsyncClient, syntactically_invalid_email: str
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
            self, parseable_email: str, client: AsyncClient
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


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_success(
        self,
        client: AsyncClient,
        user_in_db: "User",
    ):
        login_data = {"username": TEST_USER_EMAIL,
                      "password": TEST_USER_PASSWORD}
        # if my api want the from_data(form data), I need to use data
        response = await client.post("/users/login", data=login_data)
        assert response.status_code == 200
        result = response.json()

        assert "access_token" in result
        assert result["token_type"] == "bearer"


    @pytest.mark.asyncio
    async def test_login_failed_with_nonexist(
            self,
            client: AsyncClient,
            user_in_db: "User"):
        login_data = {
            "username": "no_exist_student@example.com",
            "password": "invalid_password",
        }
        response = await client.post("/users/login", data=login_data)
        assert response.status_code == 401


    @pytest.mark.asyncio
    async def test_login_failed_with_incorrect_password(
            self,
            client: AsyncClient,
            user_in_db: "User"
    ):
        login_data = {"username": TEST_USER_EMAIL,
                      "password": "a-wrong-password123456"}
        response = await client.post("/users/login", data=login_data)
        assert response.status_code == 401


    @pytest.mark.asyncio
    async def test_access_protected_route_with_expired_token(
            self,
            client: AsyncClient,
            user_in_db: "User"
    ):
        login_data = {"username": "refresh@test.com",
                      "password": "a-secure-password123456"}

        # create an expired token
        expired_token = create_access_token(user=user_in_db,
                                            expires_delta=timedelta(minutes=-1))
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = await client.get("users/me", headers=headers)

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"


    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client: AsyncClient):
        refresh_payload = {"refresh_token": "this-is-not-a-valid-jwt"}
        response = await client.post("users/refresh", json=refresh_payload)

        assert response.status_code == 401
        assert "Invalid refresh token" in response.json()["detail"]


    # @pytest.mark.asyncio
    # async def test_refresh_with_expired_refresh_token(client: AsyncClient):
    #     # TODO: this test failed.
    #     expired_refresh_token = create_access_token(user="any@user.com",
    #                                                 expires_delta=timedelta(
    #                                                     minutes=-1))
    #     refresh_payload = {"refresh_token": expired_refresh_token}
    #     response = await client.post("/auth/refresh", json=refresh_payload)
    #
    #     assert response.status_code == 401


class TestLogout:
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
        login_data = {"username": TEST_USER_EMAIL,
                      "password": TEST_USER_PASSWORD}
        login_response = await client.post("/users/login", data=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 步骤 2: 调用登出接口
        logout_response = await client.post("/users/logout", headers=headers)

        # 步骤 3: 断言登出成功
        assert logout_response.status_code == 200
        # 假设成功登出后返回此消息，请根据您的实际 API 进行调整
        assert logout_response.json() == {"message": "Successfully logged out"}

    @pytest.mark.asyncio
    async def test_access_protected_route_after_logout(
            self,
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
        login_data = {"username": TEST_USER_EMAIL,
                      "password": TEST_USER_PASSWORD}
        login_response = await client.post("/users/login", data=login_data)
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        # 步骤 2: 登出
        logout_response = await client.post("/users/logout", headers=headers)
        assert logout_response.status_code == 200

        # 步骤 3: 使用已登出的 refresh_token 尝试刷新
        refresh_data = {"refresh_token": refresh_token}
        refresh_response = await client.post("/users/refresh",
                                             json=refresh_data)

        # 步骤 4: 断言刷新失败
        assert refresh_response.status_code == 401
        # 这个错误信息取决于你的 refresh 接口在数据库找不到匹配的 refresh_token 时的返回
        assert refresh_response.json()["detail"] == "Invalid refresh token"

    @pytest.mark.asyncio
    async def test_logout_with_invalid_token(self, client: AsyncClient):
        """
        测试使用一个无效的 token 尝试登出。
        """
        headers = {"Authorization": "Bearer this-is-an-invalid-token"}
        response = await client.post("/users/logout", headers=headers)

        assert response.status_code == 401
        assert response.json()["detail"] == "Could not validate credentials"

    @pytest.mark.asyncio
    async def test_logout_without_token(self, client: AsyncClient):
        """
        测试在未提供 token 的情况下请求登出接口。
        """
        response = await client.post("/users/logout")

        # FastAPI 在缺少 Authorization header 时通常会返回 401
        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"
