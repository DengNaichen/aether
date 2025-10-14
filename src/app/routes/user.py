from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import core, models, schemas
from src.app.core.deps import get_current_active_user, get_db
from src.app.crud.user import create_user, get_user_by_email
from src.app.schemas.user import UserCreate, UserRead

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.get("/me", response_model=schemas.user.UserRead)
async def read_users_me(
    current_user: models.user.User = Depends(get_current_active_user),
):
    return current_user
