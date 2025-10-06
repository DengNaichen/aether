from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager
from datetime import timedelta

from app.core.database import get_db, engine
# from app.models.models import Base, Student
# from app.schemas.schemas import StudentCreate, StudentOut, Token, UserLogin, EnrollmentCreate
from app.core.security import verify_password, ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token
from src.app.routes import student
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

app.include_router(student.router)
# @app.post("/register", response_model=StudentOut,
#           status_code=status.HTTP_201_CREATED)
# async def register_student(student_data: StudentCreate,
#                            db: AsyncSession = Depends(get_db)):
#     # check if the email exists
#     existing_student = await get_student_by_email(db=db,
#                                                   email=student_data.email)
#
#     # error handling in api layer
#     if existing_student:
#         raise HTTPException(
#             status_code=400,
#             detail="Email already registered"
#         )
#     # add student to a database
#     new_student = await create_student(db=db, student_data=student_data)
#     return new_student


@app.get("/students")
# async def list_students(db: AsyncSession = Depends(get_db)):
#     result = await db.execute(select(Student))
#     students = result.scalars().all()
#     return students


# @app.post("/login", response_model=Token)
# async def login_for_access_token(user_credentials: UserLogin,
#                                  db: AsyncSession = Depends(get_db)):
#     # search user based on email
#     # TODO: add more status code here
#     result = await db.execute(
#         select(Student).where(Student.email == user_credentials.email)
#     )
#     db_student = result.scalars().first()
#
#     # check if a user exists and if the password corrects
#     if not db_student or not verify_password(user_credentials.password,
#                                              db_student.password_hashed):
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Incorrect email or password",
#             headers={"WWW-Authenticate": "Bearer"},
#         )
#
#     # if passed the verification, create jwt
#     access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     access_token = create_access_token(
#         data={"sub": db_student.email},
#         expires_delta=access_token_expires
#     )
#
#     return {"access_token": access_token, "token_type": "bearer"}
#
#
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
