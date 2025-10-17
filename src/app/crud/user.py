import uuid
from uuid import UUID
from typing import Union

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.core.security import get_password_hash
from src.app.models.user import User
from src.app.schemas.user import UserCreate, AdminUserCreate


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


async def create_user(
        db: AsyncSession,
        *,
        user_in: Union[UserCreate, AdminUserCreate]        
) -> User:
    """Create a new user in the database.
    This function is flexible to accept either UserCreate or AdminUserCreate 
    schemas.    

    Args:
        db (AsyncSession): The database session.
        user_in (UserCreate | AdminUserCreate): The user data for creating
            a new user.

    Returns:
        User: The created user object.
    """
    # convert a new user in the database
    user_data = user_in.model_dump(exclude={"password"})

    # hashed the password before storing
    hashed_password = get_password_hash(user_in.password)
    user_data["hashed_password"] = hashed_password

    # create the user model instance using the dictionary
    # The **user_data unpacks the dictionary into keyword arguments
    # This automatically includes fields like is_admin if they exist
    new_user = User(**user_data)
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_refresh_token(
    db: AsyncSession, *, user_id: uuid.UUID, token: str | None
) -> User | None:
    """Update the refresh token for a user.

    Args:
        db (AsyncSession): The database session.
        user_id (uuid.UUID): The unique identifier of the user.
        token (str | None): The new refresh token to set, or None to clear it.

    Returns:
        User | None: The updated user object if found, otherwise None.
            
    """
    user = await db.get(User, user_id)
    if not user:
        return None
    user.refresh_token = token
    await db.commit()
    await db.refresh(user)
    return user
