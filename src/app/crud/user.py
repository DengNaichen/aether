import uuid
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from src.app.core.security import get_password_hash
from src.app.models.user import User
from src.app.schemas.user import UserCreate


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await db.execute(statement)
    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> User | None:
    """
    Args:
        db:
        user_id:

    Returns:
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def create_user(user_data: UserCreate, db: AsyncSession) -> User:
    # hash the password
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        name=user_data.name,
        email=user_data.email,
        hashed_password=hashed_password,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_refresh_token(
    db: AsyncSession, *, user_id: uuid.UUID, token: str | None
) -> User | None:
    user = await db.get(User, user_id)
    if not user:
        return None
    user.refresh_token = token
    await db.commit()
    await db.refresh(user)
    return user
