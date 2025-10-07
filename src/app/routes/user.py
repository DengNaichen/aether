from fastapi import FastAPI, Depends, status, HTTPException, APIRouter
from src.app.schemas.user import UserRead, UserCreate
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.crud.user import get_user_by_email, create_user
from src.app.core.database import get_db

router = APIRouter(
    prefix="/user",
    tags=["User"],
)


@router.post("/register",
             response_model=UserRead,
             status_code=status.HTTP_201_CREATED)
async def register_student(
        user_data: UserCreate,
        db: AsyncSession = Depends(get_db)
):
    existing_user = await get_user_by_email(db=db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    new_user = await create_user(db=db, user_data=user_data)
    return new_user
