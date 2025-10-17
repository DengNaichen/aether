from fastapi import APIRouter, status
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.core.deps import get_db, get_current_admin_user
from src.app.crud.user import create_user
from src.app.schemas.user import AdminUserCreate, UserRead
from src.app.models.user import User
from src.app import crud

router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.post(
    "/users/",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new admin user",
)
async def create_admin_user(
    *,
    user_in: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    current_admin: User = Depends(get_current_admin_user)
):
    """Create a new admin user.

    This endpoint all
    """
    user = await crud.user.get_user_by_email(db=db, email=user_in.email)

    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already exists",
        )

    new_user = await crud.user.create_user(db=db, user_in=user_in)
    return new_user
        