import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from neo4j import AsyncNeo4jDriver
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import db_manager
from app.crud.user import get_user_by_id
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


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


async def get_neo4j_driver() -> AsyncNeo4jDriver:
    """
    Dependency to get the Neo4j driver.
    Returns:
        AsyncNeo4jDriver: An asynchronous Neo4j driver.
    Raises:
        HTTPException: If the Neo4j driver is not available.
    """
    driver = db_manager.neo4j_driver
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j Driver is not available",
        )
    return driver


async def get_current_user(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
) -> User:
    """
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
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise credentials_exception

    user = await get_user_by_id(db=db, user_id=user_uuid)
    if user is None:
        raise credentials_exception
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
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Inactive user")
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
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient privileges"
        )
    return current_user
