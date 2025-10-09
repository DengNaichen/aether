import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from neo4j import AsyncNeo4jDriver

from src.app.core.settings import settings
from src.app.core.database import AsyncSessionLocal
from src.app.crud.user import get_user_by_email, get_user_by_id
from src.app.main import db_connections
from src.app.models.user import User


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_neo4j_driver(request: Request) -> AsyncNeo4jDriver:
    driver = db_connections.neo4j_driver
    if driver is None:
        raise HTTPException(status_code=503, detail="Neo4j Driver is not avaliable")
    return driver


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")


async def get_current_user(
        db: AsyncSession = Depends(get_db),
        token: str = Depends(oauth2_scheme)
) -> User:
    print(f"➡️ [Backend] Received a token for validation. Token starts with: {token}...")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        print(f"✅ [Backend] JWT Decoded Successfully. Payload: {payload}")
        user_id: str = payload.get("sub")
        if user_id is None:
            print("🛑 [Backend] Token payload does not contain 'sub' (user ID).")
            raise credentials_exception
    except JWTError as e:
        print(f"🛑 [Backend] JWT Validation Error: {type(e).__name__} - {e}")
        raise credentials_exception

    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        print(f"🛑 [Backend] The 'sub' claim '{user_id}' is not a valid UUID.")
        raise credentials_exception

    user = await get_user_by_id(db=db, user_id=user_uuid)
    if user is None:
        print(f"🛑 [Backend] User not found in DB for ID: {user_id}")
        raise credentials_exception
    return user


async def get_current_active_user(
        current_user: User = Depends(get_current_user)
) -> User:
    return current_user
