import uuid
from uuid import UUID
from typing import Union

from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate, AdminUserCreate


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


async def set_reset_token(
    db: AsyncSession,
    *,
    user_id: UUID,
    hashed_token: str,
    expires_at: any
) -> User | None:
    """
    Set a password reset token for a user.

    Args:
        db (AsyncSession): The database session.
        user_id (UUID): The unique identifier of the user.
        hashed_token (str): The hashed reset token to store.
        expires_at (datetime): When the token expires.

    Returns:
        User | None: The updated user object if found, otherwise None.

    Example:
        >>> from datetime import datetime, timedelta, timezone
        >>> expires = datetime.now(timezone.utc) + timedelta(hours=1)
        >>> user = await set_reset_token(
        ...     db, user_id=user.id,
        ...     hashed_token=hashed,
        ...     expires_at=expires
        ... )
    """
    user = await db.get(User, user_id)
    if not user:
        return None

    user.reset_token = hashed_token
    user.reset_token_expires_at = expires_at
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_reset_token(
    db: AsyncSession,
    hashed_token: str
) -> User | None:
    """
    Find a user by their hashed password reset token.

    This function performs a direct O(1) database lookup using the token index.
    It also checks that the token hasn't expired.

    Args:
        db (AsyncSession): The database session.
        hashed_token (str): The SHA-256 hashed reset token.

    Returns:
        User | None: The user object if found and token not expired, None otherwise.

    Example:
        >>> from app.core.security import hash_reset_token
        >>> from datetime import datetime, timezone
        >>> plain_token = "abc123xyz..."  # From user's reset link
        >>> hashed = hash_reset_token(plain_token)
        >>> user = await get_user_by_reset_token(db, hashed)
        >>> if user:
        ...     # Token is valid and not expired, can reset password
    """
    from datetime import datetime, timezone

    result = await db.execute(
        select(User).where(
            User.reset_token == hashed_token,
            User.reset_token_expires_at > datetime.now(timezone.utc)
        )
    )
    return result.scalar_one_or_none()


async def clear_reset_token(
    db: AsyncSession,
    user_id: UUID
) -> User | None:
    """
    Clear the password reset token after successful reset.

    Args:
        db (AsyncSession): The database session.
        user_id (UUID): The unique identifier of the user.

    Returns:
        User | None: The updated user object if found, otherwise None.
    """
    user = await db.get(User, user_id)
    if not user:
        return None

    user.reset_token = None
    user.reset_token_expires_at = None
    await db.commit()
    await db.refresh(user)
    return user


async def update_password(
    db: AsyncSession,
    user_id: UUID,
    new_password: str
) -> User | None:
    """
    Update a user's password.

    Args:
        db (AsyncSession): The database session.
        user_id (UUID): The unique identifier of the user.
        new_password (str): The new password (will be hashed).

    Returns:
        User | None: The updated user object if found, otherwise None.
    """
    user = await db.get(User, user_id)
    if not user:
        return None

    user.hashed_password = get_password_hash(new_password)
    await db.commit()
    await db.refresh(user)
    return user
