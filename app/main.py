from fastapi import FastAPI, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager
from datetime import timedelta

from app.database import get_db, engine
from app.models import Base, Student
from app.schemas import StudentCreate, StudentOut, Token, UserLogin
from app.security import get_password_hash, verify_password, \
    ACCESS_TOKEN_EXPIRE_MINUTES, create_access_token


# 定义 lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时执行
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # 关闭时执行
    await engine.dispose()


# 把 lifespan 传给 FastAPI
app = FastAPI(lifespan=lifespan)


@app.post("/register", response_model=StudentOut,
          status_code=status.HTTP_201_CREATED)
# @app.post("/register", status_code=status.HTTP_201_CREATED)
async def register_student(student: StudentCreate,
                           db: AsyncSession = Depends(get_db)):
    # Check if the email already exists
    result = await db.execute(
        select(Student).where(Student.email == student.email))
    existing_student = result.scalars().first()
    if existing_student:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    # Hash the password
    hashed_password = get_password_hash(student.password)

    new_student = Student(
        name=student.name,
        email=student.email,
        password_hash=hashed_password
        # In a real app, hash the password before storing it
    )
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student


@app.get("/students")
async def list_students(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student))
    students = result.scalars().all()
    return students


@app.post("/login", response_model=Token)
async def login_for_access_token(user_credentials: UserLogin,
                                 db: AsyncSession = Depends(get_db)):
    # search user based on email
    result = await db.execute(
        select(Student).where(Student.email == user_credentials.email)
    )
    db_student = result.scalars().first()

    # check if user exist and if password correct
    if not db_student or not verify_password(user_credentials.password,
                                             db_student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # if passed the verification, create jwt
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_student.email},
        expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL run successfully"}
