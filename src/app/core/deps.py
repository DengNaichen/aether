import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from neo4j import AsyncNeo4jDriver
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.config import settings
from src.app.core.database import db_manager

# from src.app.core.database import AsyncSessionLocal
from src.app.crud.user import get_user_by_email, get_user_by_id

# from src.app.main import db_connections
from src.app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # provide the database session
    async with db_manager.get_session() as session:
        try:
            yield session
        finally:
            pass


async def get_neo4j_driver() -> AsyncNeo4jDriver:
    driver = db_manager.neo4j_driver
    if driver is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Neo4j Driver is not available",
        )
    return driver


async def get_current_user(
    db: AsyncSession = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:

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
    return current_user
