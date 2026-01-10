import logging
import time
import uuid
from collections.abc import AsyncGenerator

import requests
from fastapi import Depends, HTTPException, Path, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwk, jwt
from redis.asyncio import Redis
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import db_manager
from app.crud.knowledge_graph import get_graph_by_id
from app.crud.user import get_user_by_id
from app.models.user import User
from app.worker.config import WorkerContext

logger = logging.getLogger(__name__)

oauth2_scheme = HTTPBearer(auto_error=False)
_JWKS_CACHE: dict | None = None
_JWKS_CACHE_EXPIRES_AT: float = 0.0


# ============================================================================
# Helper Functions
# ============================================================================


def _fetch_jwks() -> dict | None:
    global _JWKS_CACHE
    global _JWKS_CACHE_EXPIRES_AT

    jwks_url = settings.supabase_jwks_url
    if not jwks_url:
        logger.error("Missing SUPABASE_URL or SUPABASE_JWKS_URL for JWKS fetch")
        return None

    now = time.monotonic()
    if _JWKS_CACHE and now < _JWKS_CACHE_EXPIRES_AT:
        return _JWKS_CACHE

    try:
        response = requests.get(jwks_url, timeout=2)
        response.raise_for_status()
        jwks = response.json()
    except requests.RequestException:
        logger.exception("Failed to fetch JWKS from %s", jwks_url)
        return None

    if not isinstance(jwks, dict) or "keys" not in jwks:
        logger.error("Invalid JWKS response from %s", jwks_url)
        return None

    _JWKS_CACHE = jwks
    _JWKS_CACHE_EXPIRES_AT = now + settings.JWKS_CACHE_TTL_SECONDS
    return jwks


def _select_jwk(jwks: dict, kid: str | None, alg: str) -> dict | None:
    keys = jwks.get("keys") if isinstance(jwks, dict) else None
    if not isinstance(keys, list):
        return None

    if kid:
        for key in keys:
            if key.get("kid") == kid:
                return key

    if len(keys) == 1:
        return keys[0]

    for key in keys:
        if key.get("alg") == alg:
            return key

    return None


def _decode_jwt_token(token: str) -> dict | None:
    """
    Decode and validate a JWT token.

    Args:
        token: JWT access token string

    Returns:
        dict: JWT payload if valid, None if invalid
    """
    global _JWKS_CACHE_EXPIRES_AT
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        return None

    alg = header.get("alg")
    if alg in (None, "HS256"):
        try:
            return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=[settings.ALGORITHM],
                audience="authenticated",
            )
        except JWTError:
            return None

    if alg in ("ES256", "RS256"):
        jwks = _fetch_jwks()
        if not jwks:
            return None

        key = _select_jwk(jwks, header.get("kid"), alg)
        if not key:
            logger.error("No matching JWK found for kid=%s", header.get("kid"))
            _JWKS_CACHE_EXPIRES_AT = 0.0
            jwks = _fetch_jwks()
            key = _select_jwk(jwks or {}, header.get("kid"), alg)
            if not key:
                return None

        try:
            public_key = jwk.construct(key, alg)
            public_key_pem = public_key.to_pem().decode("utf-8")
            return jwt.decode(
                token,
                public_key_pem,
                algorithms=[alg],
                audience="authenticated",
            )
        except JWTError:
            return None
        except Exception:
            logger.exception("Failed to construct public key for JWT verification")
            return None

    logger.error("Unsupported JWT algorithm: %s", alg)
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
    if user is not None:
        return user, None

    email = payload.get("email")
    if not email:
        return None, f"User not found in database: {user_id_str}"

    name = None
    user_metadata = payload.get("user_metadata")
    if isinstance(user_metadata, dict):
        name = user_metadata.get("full_name") or user_metadata.get("name")

    user = User(id=user_uuid, email=email, name=name)
    db.add(user)
    try:
        await db.commit()
        await db.refresh(user)
        logger.info("Auto-provisioned user %s", user.email)
        return user, None
    except SQLAlchemyError:
        await db.rollback()
        logger.exception("Failed to auto-provision user %s", user_id_str)
        return None, f"User not found in database: {user_id_str}"


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
