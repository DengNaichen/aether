import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.conftest import (TEST_USER_EMAIL, TEST_ADMIN_EMAIL,
                            TEST_USER_NAME, TEST_USER_PASSWORD)


class TestCreateUserByAdmin:

    @pytest.mark.asyncio
    async def test_admin_can_create_normal_user(
            self,
            authenticated_admin_client: AsyncClient,
    ):
        """管理员成功创建一个普通用户"""
        new_user_data = {
            "name": "New Normal User",
            "email": "new.normal@example.com",
            "password": "new_password",
            "is_admin": False,  # 显式指定为 False
        }
        response = await authenticated_admin_client.post(
            f"/admin/users/", json=new_user_data
        )
        assert response.status_code == 201

        data = response.json()
        assert data["email"] == new_user_data["email"]
        assert data["name"] == new_user_data["name"]
        assert data["is_admin"] is False
        assert "id" in data

    @pytest.mark.asyncio
    async def test_admin_can_create_another_admin(
            self,
            authenticated_admin_client: AsyncClient,
    ):
        new_admin_data = {
            "name": "New Admin User",
            "email": "new.admin@example.com",
            "password": "new_password",
            "is_admin": True,  # 显式指定为 True
        }
        response = await authenticated_admin_client.post(
            f"/admin/users/", json=new_admin_data
        )
        assert response.status_code == 201
        data = response.json()
        assert data["email"] == new_admin_data["email"]
        assert data["is_admin"] is True

    @pytest.mark.asyncio
    async def test_normal_user_cannot_create_user(
            self,
            authenticated_client: AsyncClient
    ):
        """普通用户尝试创建用户，应该返回 403 Forbidden"""
        new_user_data = {
            "name": "some user",
            "email": "some.user@example.com",
            "password": "password"
        }
        response = await authenticated_client.post(
            f"/admin/users/", json=new_user_data
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_unauthenticated_user_cannot_create_user(
            self, client: AsyncClient
    ):
        """未登录用户尝试创建用户，应该返回 401 Unauthorized"""
        new_user_data = {
            "name": "some user",
            "email": "some.user@example.com",
            "password": "password"
        }
        response = await client.post(
            f"/admin/users/", json=new_user_data
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_admin_cannot_create_user_with_existing_email(
            self,
            authenticated_admin_client: AsyncClient,
            admin_in_db: AsyncSession,
    ):
        duplicate_email_data = {
            "name": "Another Admin",
            "email": TEST_ADMIN_EMAIL,
            "password": "password",
            "is_admin": True
        }
        response = await authenticated_admin_client.post(
            f"/admin/users/", json=duplicate_email_data
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
