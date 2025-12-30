"""
Comprehensive unit tests for app.core.deps module.

Tests cover:
- JWT helper functions (_decode_jwt_token, _get_user_from_payload)
- Authentication dependencies (get_current_user, get_current_active_user, get_current_admin_user)
- Optional authentication (get_optional_user)
- Resource access dependencies (get_owned_graph, get_public_graph)
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import (
    _decode_jwt_token,
    _get_user_from_payload,
    get_current_admin_user,
    get_current_active_user,
    get_current_user,
    get_optional_user,
    get_owned_graph,
    get_public_graph,
)
from app.models.user import User


# ============================================================================
# Helper Function: Create JWT Tokens
# ============================================================================


def create_test_token(user_id: uuid.UUID, expires_delta: timedelta | None = None) -> str:
    """Create a test JWT token for the given user ID."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=30)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "aud": "authenticated",
    }

    token = jwt.encode(
        payload,
        settings.SUPABASE_JWT_SECRET,
        algorithm=settings.ALGORITHM,
    )
    return token


# ============================================================================
# Test Class: JWT Decoding Helper
# ============================================================================


class TestDecodeJwtToken:
    """Test the _decode_jwt_token helper function."""

    def test_valid_token_returns_payload(self, user_in_db: User):
        """Test that a valid JWT token is decoded successfully."""
        token = create_test_token(user_in_db.id)
        payload = _decode_jwt_token(token)

        assert payload is not None
        assert payload["sub"] == str(user_in_db.id)
        assert payload["aud"] == "authenticated"

    def test_invalid_token_returns_none(self):
        """Test that an invalid token returns None."""
        invalid_token = "this.is.not.a.valid.token"
        payload = _decode_jwt_token(invalid_token)
        assert payload is None

    def test_expired_token_returns_none(self, user_in_db: User):
        """Test that an expired token returns None."""
        # Create token that expired 1 hour ago
        expired_token = create_test_token(user_in_db.id, expires_delta=timedelta(hours=-1))
        payload = _decode_jwt_token(expired_token)
        assert payload is None

    def test_malformed_token_returns_none(self):
        """Test that a malformed token returns None."""
        malformed_tokens = [
            "",
            "not-a-jwt",
            "eyJ.invalid",
            "a.b.c",
        ]

        for token in malformed_tokens:
            payload = _decode_jwt_token(token)
            assert payload is None, f"Expected None for malformed token: {token}"

    def test_wrong_algorithm_token_returns_none(self, user_in_db: User):
        """Test that a token signed with wrong algorithm returns None."""
        payload = {
            "sub": str(user_in_db.id),
            "aud": "authenticated",
        }
        # Sign with HS384 instead of HS256
        wrong_algo_token = jwt.encode(payload, "wrong-secret", algorithm="HS384")
        result = _decode_jwt_token(wrong_algo_token)
        assert result is None


# ============================================================================
# Test Class: Get User From Payload Helper
# ============================================================================


class TestGetUserFromPayload:
    """Test the _get_user_from_payload helper function."""

    @pytest.mark.asyncio
    async def test_valid_payload_returns_user(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Test extracting user from valid JWT payload."""
        payload = {"sub": str(user_in_db.id)}
        user, error = await _get_user_from_payload(test_db, payload)

        assert user is not None
        assert error is None
        assert user.id == user_in_db.id
        assert user.email == user_in_db.email

    @pytest.mark.asyncio
    async def test_missing_sub_returns_error(self, test_db: AsyncSession):
        """Test that missing 'sub' field returns error."""
        payload = {"other_field": "value"}
        user, error = await _get_user_from_payload(test_db, payload)

        assert user is None
        assert error == "No user_id in token payload"

    @pytest.mark.asyncio
    async def test_invalid_uuid_returns_error(self, test_db: AsyncSession):
        """Test that invalid UUID format returns error."""
        payload = {"sub": "not-a-valid-uuid"}
        user, error = await _get_user_from_payload(test_db, payload)

        assert user is None
        assert error == "Invalid UUID format"

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_error(self, test_db: AsyncSession):
        """Test that non-existent user ID returns error."""
        nonexistent_id = uuid.uuid4()
        payload = {"sub": str(nonexistent_id)}
        user, error = await _get_user_from_payload(test_db, payload)

        assert user is None
        assert error == f"User not found in database: {nonexistent_id}"


# ============================================================================
# Test Class: Get Current User
# ============================================================================


class TestGetCurrentUser:
    """Test the get_current_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_credentials_returns_user(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Test that valid credentials return the authenticated user."""
        token = create_test_token(user_in_db.id)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Mock request object
        request = Mock()
        request.headers.get.return_value = f"Bearer {token}"

        user = await get_current_user(request, test_db, credentials)

        assert user is not None
        assert user.id == user_in_db.id
        assert user.email == user_in_db.email

    @pytest.mark.asyncio
    async def test_no_credentials_raises_exception(self, test_db: AsyncSession):
        """Test that missing credentials raises 401."""
        request = Mock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, test_db, None)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Could not validate credentials" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_invalid_token_raises_exception(self, test_db: AsyncSession):
        """Test that invalid token raises 401."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token.here"
        )
        request = Mock()
        request.headers.get.return_value = "Bearer invalid.token.here"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, test_db, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_expired_token_raises_exception(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Test that expired token raises 401."""
        expired_token = create_test_token(user_in_db.id, expires_delta=timedelta(hours=-1))
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=expired_token
        )
        request = Mock()
        request.headers.get.return_value = f"Bearer {expired_token}"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, test_db, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_nonexistent_user_raises_exception(self, test_db: AsyncSession):
        """Test that token for non-existent user raises 401."""
        nonexistent_id = uuid.uuid4()
        token = create_test_token(nonexistent_id)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()
        request.headers.get.return_value = f"Bearer {token}"

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, test_db, credentials)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================================================
# Test Class: Get Current Active User
# ============================================================================


class TestGetCurrentActiveUser:
    """Test the get_current_active_user dependency."""

    @pytest.mark.asyncio
    async def test_active_user_returns_user(self, user_in_db: User):
        """Test that active user is returned successfully."""
        # user_in_db is active by default
        assert user_in_db.is_active is True

        user = await get_current_active_user(user_in_db)
        assert user.id == user_in_db.id

    @pytest.mark.asyncio
    async def test_inactive_user_raises_exception(self, test_db: AsyncSession):
        """Test that inactive user raises 401."""
        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            name="Inactive User",
            is_active=False,
        )
        test_db.add(inactive_user)
        await test_db.commit()
        await test_db.refresh(inactive_user)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_active_user(inactive_user)

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Inactive user" in str(exc_info.value.detail)


# ============================================================================
# Test Class: Get Current Admin User
# ============================================================================


class TestGetCurrentAdminUser:
    """Test the get_current_admin_user dependency."""

    @pytest.mark.asyncio
    async def test_admin_user_returns_user(self, admin_in_db: User):
        """Test that admin user is returned successfully."""
        assert admin_in_db.is_admin is True

        user = await get_current_admin_user(admin_in_db)
        assert user.id == admin_in_db.id

    @pytest.mark.asyncio
    async def test_regular_user_raises_exception(self, user_in_db: User):
        """Test that regular user raises 403."""
        assert user_in_db.is_admin is False

        with pytest.raises(HTTPException) as exc_info:
            await get_current_admin_user(user_in_db)

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "Insufficient privileges" in str(exc_info.value.detail)


# ============================================================================
# Test Class: Get Optional User
# ============================================================================


class TestGetOptionalUser:
    """Test the get_optional_user dependency."""

    @pytest.mark.asyncio
    async def test_valid_credentials_returns_user(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Test that valid credentials return the user."""
        token = create_test_token(user_in_db.id)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()

        user = await get_optional_user(request, test_db, credentials)

        assert user is not None
        assert user.id == user_in_db.id

    @pytest.mark.asyncio
    async def test_no_credentials_returns_none(self, test_db: AsyncSession):
        """Test that no credentials returns None instead of raising."""
        request = Mock()
        user = await get_optional_user(request, test_db, None)
        assert user is None

    @pytest.mark.asyncio
    async def test_invalid_token_returns_none(self, test_db: AsyncSession):
        """Test that invalid token returns None instead of raising."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token"
        )
        request = Mock()

        user = await get_optional_user(request, test_db, credentials)
        assert user is None

    @pytest.mark.asyncio
    async def test_expired_token_returns_none(
        self, test_db: AsyncSession, user_in_db: User
    ):
        """Test that expired token returns None instead of raising."""
        expired_token = create_test_token(user_in_db.id, expires_delta=timedelta(hours=-1))
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=expired_token
        )
        request = Mock()

        user = await get_optional_user(request, test_db, credentials)
        assert user is None

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_none(self, test_db: AsyncSession):
        """Test that token for non-existent user returns None."""
        nonexistent_id = uuid.uuid4()
        token = create_test_token(nonexistent_id)
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = Mock()

        user = await get_optional_user(request, test_db, credentials)
        assert user is None


# ============================================================================
# Test Class: Get Owned Graph
# ============================================================================


class TestGetOwnedGraph:
    """Test the get_owned_graph dependency."""

    @pytest.mark.asyncio
    async def test_owner_can_access_graph(
        self,
        test_db: AsyncSession,
        user_in_db: User,
        private_graph_in_db,
    ):
        """Test that graph owner can access their graph."""
        graph = await get_owned_graph(
            graph_id=private_graph_in_db.id,
            db_session=test_db,
            current_user=user_in_db,
        )

        assert graph is not None
        assert graph.id == private_graph_in_db.id
        assert graph.owner_id == user_in_db.id

    @pytest.mark.asyncio
    async def test_non_owner_raises_exception(
        self,
        test_db: AsyncSession,
        other_user_in_db: User,
        private_graph_in_db,
    ):
        """Test that non-owner cannot access graph."""
        with pytest.raises(HTTPException) as exc_info:
            await get_owned_graph(
                graph_id=private_graph_in_db.id,
                db_session=test_db,
                current_user=other_user_in_db,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "don't have access" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_nonexistent_graph_raises_exception(
        self,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test that non-existent graph raises 404."""
        nonexistent_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await get_owned_graph(
                graph_id=nonexistent_id,
                db_session=test_db,
                current_user=user_in_db,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in str(exc_info.value.detail)


# ============================================================================
# Test Class: Get Public Graph
# ============================================================================


class TestGetPublicGraph:
    """Test the get_public_graph dependency."""

    @pytest.mark.asyncio
    async def test_public_graph_is_accessible(
        self,
        test_db: AsyncSession,
        user_in_db: User,
    ):
        """Test that public graphs can be accessed."""
        from app.models.knowledge_graph import KnowledgeGraph

        # Create a public graph
        public_graph = KnowledgeGraph(
            owner_id=user_in_db.id,
            name="Public Test Graph",
            slug="public-test-graph",
            description="Public graph for testing",
            is_public=True,
        )
        test_db.add(public_graph)
        await test_db.commit()
        await test_db.refresh(public_graph)

        graph = await get_public_graph(
            graph_id=public_graph.id,
            db_session=test_db,
        )

        assert graph is not None
        assert graph.id == public_graph.id
        assert graph.is_public is True

    @pytest.mark.asyncio
    async def test_template_graph_is_accessible(
        self,
        test_db: AsyncSession,
        template_graph_in_db,
    ):
        """Test that template graphs can be accessed."""
        graph = await get_public_graph(
            graph_id=template_graph_in_db.id,
            db_session=test_db,
        )

        assert graph is not None
        assert graph.id == template_graph_in_db.id
        assert graph.is_template is True

    @pytest.mark.asyncio
    async def test_private_graph_raises_exception(
        self,
        test_db: AsyncSession,
        private_graph_in_db,
    ):
        """Test that private graphs raise 403."""
        with pytest.raises(HTTPException) as exc_info:
            await get_public_graph(
                graph_id=private_graph_in_db.id,
                db_session=test_db,
            )

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "private" in str(exc_info.value.detail).lower()

    @pytest.mark.asyncio
    async def test_nonexistent_graph_raises_exception(self, test_db: AsyncSession):
        """Test that non-existent graph raises 404."""
        nonexistent_id = uuid.uuid4()

        with pytest.raises(HTTPException) as exc_info:
            await get_public_graph(
                graph_id=nonexistent_id,
                db_session=test_db,
            )

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in str(exc_info.value.detail)
