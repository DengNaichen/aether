from fastapi import FastAPI, Depends, status, HTTPException, APIRouter
from src.app.schemas.user import UserRead, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.crud.user import get_user_by_email, create_user
from src.app.core.database import get_db

from src.app import core

from src.app import models, schemas
from src.app.core.deps import get_current_active_user

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.get("/me", response_model=schemas.user.UserRead)
async def read_users_me(
    current_user: models.user.User = Depends(get_current_active_user)
):
    return current_user



