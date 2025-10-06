from fastapi import FastAPI, Depends, status, HTTPException, APIRouter
from src.app.schemas.student import StudentRead, StudentCreate
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.crud.student import get_student_by_email, create_student

from src.app.core.database import get_db

# def get_db():
#     pass


router = APIRouter(
    prefix="/students",
    tags=["Students"],
)


@router.post("/register",
             response_model=StudentRead,
             status_code=status.HTTP_201_CREATED)
async def register_student(
        student_data: StudentCreate,
        db: AsyncSession = Depends(get_db)
):
    existing_student = await get_student_by_email(db=db,
                                                  email=student_data.email)
    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )
    new_student = await create_student(db=db, student_data=student_data)
    return new_student
