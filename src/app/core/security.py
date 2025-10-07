from passlib.context import CryptContext
from typing import Any, Union
from datetime import datetime, timedelta, timezone
from jose import jwt
from app.core.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.user import User
from src.app import crud

# set hashed context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# jwt configuration
SECERT_KEY = settings.SECRET_KEY
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """verify if the plain password matches the hashed password"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: Union[str, Any],
                        expires_delta: timedelta | None = None) -> str:
    """create JWT based on the expired data and user info"""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECERT_KEY, algorithm=ALGORITHM)

    return encoded_jwt


# TODO: should I use EmailStr here ?
async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    User verification function
    """
    user = await crud.user.get_user_by_email(db, email=email)

    # if the user doesn't exist, return None
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
