import pytest
from httpx import AsyncClient
from starlette import status

from app.models.user import User


class TestUserMe:
    @pytest.mark.asyncio
    async def test_read_users_me_success(
        self, authenticated_client: AsyncClient, user_in_db: User
    ):
        """Test retrieving current user profile."""
        response = await authenticated_client.get("/users/me")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == user_in_db.email
        assert data["id"] == str(user_in_db.id)
        # Ensure password is not returned
        assert "password" not in data
        assert "hashed_password" not in data

    @pytest.mark.asyncio
    async def test_read_users_me_unauthorized(self, client: AsyncClient):
        """Test accessing profile without token fails."""
        response = await client.get("/users/me")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
