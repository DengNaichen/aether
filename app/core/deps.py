import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import db_manager
from app.crud.user import get_user_by_id
from app.models.user import User
from app.worker.config import WorkerContext

logger = logging.getLogger(__name__)

oauth2_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a SQLAlchemy async session.
    Yields:
        AsyncSession: An asynchronous database session.
    """
    async with db_manager.get_sql_session() as session:
        try:
            yield session
        finally:
            pass


async def get_redis_client() -> Redis:
    """
    Dependency to get a Redis client from the connection pool.
    Returns:
        Redis: An asynchronous Redis client.
    """
    return db_manager.redis_client


async def get_worker_context() -> AsyncGenerator[WorkerContext, None]:
    ctx = WorkerContext(db_manager)

    try:
        yield ctx
    finally:
        pass


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> User:
    """
    TODO: update this docstring
    Retrieves the current authenticated user from a JWT access token.

    This asynchronously dependency decodes and validates the provided JWT token,
    extracts the user ID from the payload, and fetches the corresponding user
    record from the database. If the token is invalid, expired, or the user
    does not exist, an HTTP 401 Unauthorized response is raised.

    Args:
        db(AsyncSession): SQLAlchemy async database session, injected by FastAPI
            dependency system via `Depends(get_db)`.
        token(str): JWT access token extracted from the 'Authorization'
            header using the `oauth2_scheme` dependency.

    Returns:
        user (User): User object corresponding to the token subject.

    Raises:
        HTTPException: If user does not exist or token is invalid.
        ValueError: If user ID is not a valid UUID
    """
    # Debug: Log raw Authorization header
    token = credentials.credentials
    auth_header = request.headers.get("Authorization", "NOT FOUND")
    logger.debug(
        f"Authorization header: {auth_header[:50] if len(auth_header) > 50 else auth_header}..."
    )
    logger.debug("get_current_user called")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # Debug: Log token validation attempt
        token_preview = token[:20] if len(token) > 20 else token
        logger.debug(f"Validating token: {token_preview}...")

        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience="authenticated",
        )

        # Debug: Log successful decode
        user_id: str = payload.get("sub")
        logger.debug(f"Token decoded successfully, user_id: {user_id}")

        if user_id is None:
            logger.error("No user_id in token payload")
            raise credentials_exception
    except JWTError as e:
        logger.error(f"JWT decode error: {e}")
        raise credentials_exception from e

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError as e:
        logger.error(f"Invalid UUID format: {e}")
        raise credentials_exception from e

    user = await get_user_by_id(db=db, user_id=user_uuid)
    if user is None:
        logger.error(f"User not found in database: {user_uuid}")
        raise credentials_exception

    logger.info(f"User authenticated successfully: {user.email}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures that the current user is active.
    Args:
        current_user (User): The currently authenticated user, injected by
            FastAPI dependency system via `Depends(get_current_user)`.
    Returns:
        User: The active user object.
    Raises:
        HTTPException: If the user is inactive.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures that the current user has admin privileges.
    Args:
        current_user (User): The currently authenticated user, injected by
            FastAPI dependency system via `Depends(get_current_user)`.
    Returns:
        User: The admin user object.
    Raises:
        HTTPException: If the user is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient privileges"
        )
    return current_user


async def get_optional_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials | None = Depends(oauth2_scheme),
) -> User | None:
    """
    Retrieves the current authenticated user from a JWT access token if present.
    Returns None if no token or invalid token.
    """
    if not credentials:
        return None

    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience="authenticated",
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None

        user_uuid = uuid.UUID(user_id)
        user = await get_user_by_id(db=db, user_id=user_uuid)
        return user
    except (JWTError, ValueError):
        return None
