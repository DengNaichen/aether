import logging
import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import db_manager
from app.crud.knowledge_graph import get_graph_by_id
from app.crud.user import get_user_by_id
from app.models.user import User
from app.worker.config import WorkerContext

logger = logging.getLogger(__name__)

oauth2_scheme = HTTPBearer(auto_error=False)


# ============================================================================
# Helper Functions
# ============================================================================


def _decode_jwt_token(token: str) -> dict | None:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT access token string

    Returns:
        dict: JWT payload if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=[settings.ALGORITHM],
            audience="authenticated",
        )
        return payload
    except JWTError:
        return None


async def _get_user_from_payload(
    db: AsyncSession, payload: dict
) -> tuple[User | None, str | None]:
    """
    Extract user from JWT payload and fetch from database.

    Args:
        db: Database session
        payload: Decoded JWT payload

    Returns:
        tuple: (User object or None, error message or None)
    """
    user_id_str = payload.get("sub")
    if user_id_str is None:
        return None, "No user_id in token payload"

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        return None, "Invalid UUID format"

    user = await get_user_by_id(db=db, user_id=user_uuid)
    if user is None:
        return None, f"User not found in database: {user_id_str}"

    return user, None


# ============================================================================
# Database Dependencies
# ============================================================================


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a SQLAlchemy async session.
    Yields:
        AsyncSession: An asynchronous database session.
    """
    async with db_manager.get_sql_session() as session:
        yield session


async def get_redis_client() -> Redis:
    """
    Dependency to get a Redis client from the connection pool.
    Returns:
        Redis: An asynchronous Redis client.
    """
    return db_manager.redis_client


async def get_worker_context() -> AsyncGenerator[WorkerContext, None]:
    """Dependency that provides a worker context for background tasks."""
    ctx = WorkerContext(db_manager)
    yield ctx


# ============================================================================
# Authentication Dependencies
# ============================================================================


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme),
) -> User:
    """
    Retrieves the current authenticated user from a JWT access token.

    This dependency decodes and validates the provided JWT token,
    extracts the user ID from the payload, and fetches the corresponding user
    record from the database. If the token is invalid, expired, or the user
    does not exist, an HTTP 401 Unauthorized response is raised.

    Args:
        request: FastAPI request object
        db: SQLAlchemy async database session, injected by FastAPI
            dependency system via `Depends(get_db)`
        credentials: JWT credentials extracted from the Authorization header

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

    # Check if credentials were provided
    if credentials is None:
        logger.warning("No credentials provided in request")
        raise credentials_exception

    token = credentials.credentials

    # Decode JWT token
    payload = _decode_jwt_token(token)
    if payload is None:
        logger.error("JWT decode failed")
        raise credentials_exception

    # Extract and validate user
    user, error = await _get_user_from_payload(db, payload)
    if error:
        logger.error(error)
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

    This is a non-throwing version of get_current_user that returns None
    instead of raising an exception when authentication fails.

    Args:
        request: FastAPI request object
        db: Database session
        credentials: Optional JWT credentials

    Returns:
        User object if authentication succeeds, None otherwise
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Decode JWT token
    payload = _decode_jwt_token(token)
    if payload is None:
        logger.debug("Optional auth: JWT decode failed")
        return None

    # Extract and validate user
    user, error = await _get_user_from_payload(db, payload)
    if error:
        logger.debug(f"Optional auth: {error}")
        return None

    return user


# ============================================================================
# Resource Access Dependencies
# ============================================================================


async def get_owned_graph(
    graph_id: uuid.UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Dependency that retrieves a knowledge graph and verifies ownership.

    This dependency combines graph fetching and ownership verification
    in a single reusable component, following the FastAPI dependency pattern.

    Args:
        graph_id: Knowledge graph UUID from path parameter
        db_session: Database session
        current_user: Authenticated active user

    Returns:
        KnowledgeGraph: The graph owned by the current user

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the user is not the owner
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found.",
        )

    if knowledge_graph.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this knowledge graph.",
        )

    return knowledge_graph


async def get_public_graph(
    graph_id: uuid.UUID = Path(..., description="Knowledge graph UUID"),
    db_session: AsyncSession = Depends(get_db),
):
    """
    Dependency that retrieves a public or template knowledge graph.

    This dependency verifies that the graph is accessible to all users
    (either public or template), without requiring ownership.

    Args:
        graph_id: Knowledge graph UUID from path parameter
        db_session: Database session

    Returns:
        KnowledgeGraph: The public or template graph

    Raises:
        HTTPException 404: If the knowledge graph doesn't exist
        HTTPException 403: If the graph is private (neither public nor template)
    """
    knowledge_graph = await get_graph_by_id(db_session=db_session, graph_id=graph_id)
    if not knowledge_graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Knowledge graph {graph_id} not found.",
        )

    if not knowledge_graph.is_public and not knowledge_graph.is_template:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This knowledge graph is private. Only public or template graphs can be accessed.",
        )

    return knowledge_graph
