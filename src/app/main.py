from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager
from datetime import timedelta

from src.app.core.database import get_db, engine
# from app.models.models import Base, Student
# from app.schemas.schemas import StudentCreate, StudentOut, Token, UserLogin, EnrollmentCreate
from app.core.security import verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from src.app.routes import user, auth
from src.app.models.base import Base

# from app.crud.crud import get_student_by_email, create_student, enroll_student_in_course


# 定义 lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


# pass lifespan tp FastAPI
app = FastAPI(lifespan=lifespan)

app.include_router(user.router)
app.include_router(auth.router)


# @app.get("/students")
# async def list_students(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Student))
#     students = result.scalars().all()
#     return students


# async def enroll_in_course_endpoint(
#     enrollment: EnrollmentCreate,
#     db: AsyncSession = Depends(get_db)
# ):
#     # from PostgeSQL obtain the complete student object
#     student = await db.get(Student, enrollment.student_id)
#     if not student:
#         raise HTTPException(status_code=404, detail="Student not found")
#     try:
#         # pass the complete student object to crud
#         await enroll_student_in_course(
#             student=student,
#             course_name=enrollment.course_name # TODO:
#         )
#         return {"status": "success", "detail":
#                  f"Student {student.name} enrolled in {enrollment.course_name}"}
#     except ValueError as e:
#         raise HTTPException(status_code=400, detail=str(e))
#     except Exception as e:
#         print(f"Error enrolling student: {e}")
#         raise HTTPException(status_code=500,
#                             detail="Failed to enroll in course")


@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL run successfully"}
