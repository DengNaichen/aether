# import uuid
from uuid import UUID
# from typing import Union

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

# from app.core.security import get_password_hash
from app.models.user import User
# from app.schemas.user import UserCreate, AdminUserCreate


async def get_user_by_email(db: AsyncSession, email: EmailStr) -> User | None:
    """Obtain a user by their email address in the database.
    
    Args:
        db (AsyncSession): The database session.
        email (str): The email address of the user to retrieve.
    Returns:
        User | None: The user object if found, otherwise None.
    """
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """ Retrieve a user by their unique ID.

    Args:
        db (AsyncSession): The database session.
        user_id (UUID): The unique identifier of the user.

    Returns:
        User | None: The user object if found, otherwise None.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()
