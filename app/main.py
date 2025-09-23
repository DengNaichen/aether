from fastapi import FastAPI, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from contextlib import asynccontextmanager

from app.database import get_db, engine
from app.models import Base, Student

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

@app.get("/students")
async def list_students(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Student))
    students = result.scalars().all()
    return students

@app.post("/students")
async def create_student(name: str, email: str, password_hash: str, db: AsyncSession = Depends(get_db)):
    new_student = Student(name = name, email = email, password_hash = password_hash)
    db.add(new_student)
    await db.commit()
    await db.refresh(new_student)
    return new_student


@app.get("/")
async def root():
    return {"message": "FastAPI + PostgreSQL 已成功运行！"}
