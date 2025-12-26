"""
Token Refresh Functionality Tests

This module tests the token refresh mechanism following TDD principles.
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import timedelta
from jose import jwt

from app.core.config import settings
from app.core.security import create_refresh_token
from app.models.user import User
from tests.conftest import TEST_USER_EMAIL, TEST_USER_PASSWORD


class TestTokenRefresh:
    """Test suite for token refresh functionality"""

    @pytest.mark.asyncio
    async def test_refresh_token_returns_both_tokens(
        self, client: AsyncClient, user_in_db: User
    ):
        """
        Test that /users/refresh returns both access_token and refresh_token

        This is the key test that will fail initially because the current
        implementation only returns access_token.
        """
        # Step 1: Login to get initial tokens
        login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        login_response = await client.post("/users/login", data=login_data)
        assert login_response.status_code == 200

        initial_tokens = login_response.json()
        initial_refresh_token = initial_tokens["refresh_token"]

        # Step 2: Use refresh token to get new tokens
        refresh_payload = {"refresh_token": initial_refresh_token}
        refresh_response = await client.post("/users/refresh", json=refresh_payload)

        # Assertions
        assert refresh_response.status_code == 200

        response_data = refresh_response.json()

        # This will fail initially - the response doesn't include refresh_token
        assert "access_token" in response_data, "Response should contain access_token"
        assert "refresh_token" in response_data, "Response should contain refresh_token"
        assert "token_type" in response_data, "Response should contain token_type"
        assert response_data["token_type"] == "bearer"

        # Verify tokens are different from initial ones
        assert response_data["access_token"] != initial_tokens["access_token"]
        assert response_data["refresh_token"] != initial_refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_invalidates_old_token(
        self, client: AsyncClient, user_in_db: User
    ):
        """
        Test that after refreshing, the old refresh_token becomes invalid

        This ensures token rotation is working properly.
        """
        # Login to get initial tokens
        login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        login_response = await client.post("/users/login", data=login_data)
        old_refresh_token = login_response.json()["refresh_token"]

        # Refresh once
        refresh_payload = {"refresh_token": old_refresh_token}
        first_refresh = await client.post("/users/refresh", json=refresh_payload)
        assert first_refresh.status_code == 200

        # Try to use the old refresh_token again - should fail
        second_refresh = await client.post("/users/refresh", json=refresh_payload)

        assert second_refresh.status_code == 401
        response_data = second_refresh.json()
        assert "detail" in response_data
        assert "Invalid refresh token" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_with_invalid_token(self, client: AsyncClient):
        """
        Test that an invalid/fake refresh token is rejected
        """
        fake_token = "totally.fake.token"
        refresh_payload = {"refresh_token": fake_token}

        response = await client.post("/users/refresh", json=refresh_payload)

        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Invalid refresh token" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_with_expired_token(
        self, client: AsyncClient, user_in_db: User
    ):
        """
        Test that an expired refresh token is rejected
        """
        # Create an expired refresh token (expired 1 day ago)
        expired_token = jwt.encode(
            {"sub": str(user_in_db.id), "exp": timedelta(days=-1)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        refresh_payload = {"refresh_token": expired_token}
        response = await client.post("/users/refresh", json=refresh_payload)

        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "Invalid refresh token" in response_data["detail"]

    @pytest.mark.asyncio
    async def test_refresh_token_saves_new_token_to_db(
        self, client: AsyncClient, user_in_db: User, db_session: AsyncSession
    ):
        """
        Test that the new refresh_token is saved to the database
        and the old one is replaced
        """
        # Login to get initial tokens
        login_data = {"username": TEST_USER_EMAIL, "password": TEST_USER_PASSWORD}
        login_response = await client.post("/users/login", data=login_data)
        old_refresh_token = login_response.json()["refresh_token"]

        # Verify old token is in DB
        await db_session.refresh(user_in_db)
        assert user_in_db.refresh_token == old_refresh_token

        # Refresh tokens
        refresh_payload = {"refresh_token": old_refresh_token}
        refresh_response = await client.post("/users/refresh", json=refresh_payload)
        assert refresh_response.status_code == 200

        new_refresh_token = refresh_response.json()["refresh_token"]

        # Verify new token is in DB and old one is replaced
        await db_session.refresh(user_in_db)
        assert user_in_db.refresh_token == new_refresh_token
        assert user_in_db.refresh_token != old_refresh_token

    @pytest.mark.asyncio
    async def test_refresh_token_with_nonexistent_user(self, client: AsyncClient):
        """
        Test that a valid token for a non-existent user is rejected
        """
        # Create a token for a non-existent user ID
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        fake_token = jwt.encode(
            {"sub": fake_user_id, "exp": timedelta(days=7)},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

        refresh_payload = {"refresh_token": fake_token}
        response = await client.post("/users/refresh", json=refresh_payload)

        assert response.status_code == 401
        response_data = response.json()
        assert "detail" in response_data
        assert "User not found" in response_data["detail"]
