import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import db_manager
from app.crud.user import get_user_by_id
from app.models.user import User
from app.worker.config import WorkerContext

# Use HTTPBearer for Supabase JWT tokens
security = HTTPBearer()


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
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> User:
    """
    Retrieves the current authenticated user from a Supabase JWT token.

    This dependency decodes and validates the provided JWT token from Supabase,
    extracts the user ID from the payload, and fetches the corresponding user
    record from the database.

    Args:
        request: FastAPI request object
        db: SQLAlchemy async database session
        credentials: JWT token from Authorization header

    Returns:
        User: User object corresponding to the token subject

    Raises:
        HTTPException: If user does not exist or token is invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        
        # Decode Supabase JWT token
        payload = jwt.decode(
            token, 
            settings.SUPABASE_JWT_SECRET, 
            algorithms=[settings.ALGORITHM]
        )

        # Supabase uses 'sub' for user ID
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError as e:
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
        current_user: The currently authenticated user
        
    Returns:
        User: The active user object
        
    Raises:
        HTTPException: If the user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Ensures that the current user has admin privileges.
    
    Args:
        current_user: The currently authenticated user
        
    Returns:
        User: The admin user object
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Insufficient privileges"
        )
    return current_user
